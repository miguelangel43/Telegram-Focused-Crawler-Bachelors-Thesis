import json
from telethon.errors import ChatAdminRequiredError
from telethon.sync import TelegramClient
from telethon.tl import functions
from telethon.errors.rpcerrorlist import ChannelPrivateError
from tqdm import tqdm
import time
import math
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
from telethon.tl.types import InputPeerChannel

# Telegram API keys
api_id = 1812168
api_hash = '57d99f51542be90739730033e553b7e8'

class SyncTelegramClient:
    def __init__(self):
        self._client = TelegramClient("session", api_id, api_hash)

    def fetch_messages(self, channel, size, max_id=None, min_id=None):
        """Method to fetch messages from a specific channel / group"""
        #TODO: first fetch the last message to find out how many messages there are in the chat
        # If there are less messages that size use the number of messages instead of size.

        params = [channel, size]
        kwargs = {}

        # The telethon module has issues if a keyword passed is None, so we will add the keyword
        # only if it is not None
        for key in ['max_id', 'min_id']:
            if locals()[key] is not None:
                kwargs[key] = locals()[key]

        with self._client as client:
            data = client.get_messages(*params, **kwargs)

        return data

    def get_channel_info(self, channel):
        with self._client as client:
            data = client(functions.channels.GetFullChannelRequest(channel=channel)).to_json()
        return json.loads(data)

    def get_channel_users(self, channel, limit=1000):
        """method to get participants from channel (we might not have privileges to get this data)
        getting some errors about permissions"""
        with self._client as client:
            try:
                participants = client.get_participants(channel, limit)
            except ChatAdminRequiredError as e:
                # TODO: ???
                raise e

        return participants

    # Returns the channel name given the id as input
    def get_channel_name(self, channel_data):
        # channel_id = 1242023007
        channel_name = channel_data["chats"][0]["username"]
        return channel_name

    def get_channel_id(self, channel_name):
        # channel_name = 'ATTILA HILDMANN OFFICIAL ⚫️⚪️🔴⚔️'
        return self.get_channel_info(str(channel_name))["full_chat"]["id"]

    def get_channel_num_participants(self, channel_data):
        return channel_data["full_chat"]["participants_count"]

    # Tries to join th channels/groups in the list that it takes as input
    def join_channels(self, new_groups):
        for group in new_groups:
            print("joining ", self.get_channel_info(group)["chats"][0]["username"])
            try:
                self._client.invoke(JoinChannelRequest(group))
            except:
                print("failed")

    """ This function does not work in Ipython """
    def find_groups_fwd(self, visited_channels, old_groups, batch_size=500):
        """Finds forwarded messages in old_groups and returns the channels those messages were sent from along with the edges.
        Args:
            visited_channels: all channels visited so far, to avoid visiting them again.
            old_groups: channels that are going to be searched for forwards. They are either the seed (in the first iteration)
                or the collected channels from the previous iteration.
        Returns:
            new_groups: the channels whose messages were forwarded to old_groups.
            new_edges: a list of lists [[ch_destination ,ch_origin]]. This means that a message was forwarded from
                ch_origin to ch_destination.
        """
        new_groups = []
        new_edges = []
        for group in tqdm(old_groups):
            # Fetch the last BATCH_SIZE messages
            messages = self.fetch_messages(
            channel=group,
            size=batch_size,
            max_id=None
            )
            for m in messages:
                # If a msg was forwarded from another channel, append it to the list
                try:
                    if m.fwd_from:
                        if hasattr(m.fwd_from ,'from_id'):
                            if hasattr(m.fwd_from.from_id, 'channel_id'):
                                new_edges.append([group, m.fwd_from.from_id.channel_id])
                                if not self.is_private(m.fwd_from.from_id.channel_id): # Just calling is_private on a private channel causes ChannelPrivateError
                                    if m.fwd_from.from_id.channel_id not in new_groups:
                                        if m.fwd_from.from_id.channel_id not in visited_channels:
                                            new_groups.append(m.fwd_from.from_id.channel_id)
                except ChannelPrivateError:
                    print(m.fwd_from.from_id.channel_id, 'is private')

        return new_groups, new_edges

    def search_query(self, channel, query):
        with self._client as client:
            ch_access_hash = client.get_entity(channel).access_hash
            channel_object = InputPeerChannel(channel_id=channel, access_hash=ch_access_hash)
            filter = InputMessagesFilterEmpty()
            result = client(SearchRequest(
                peer=channel_object,      # On which chat/conversation
                q=query,      # What to search for
                filter=filter,  # Filter to use (maybe filter for media)
                min_date=None,  # Minimum date
                max_date=None,  # Maximum date
                offset_id=0,    # ID of the message to use as offset
                add_offset=0,   # Additional offset
                limit=10,       # How many results
                max_id=0,       # Maximum message ID
                min_id=0,       # Minimum message ID
                from_id=None,    # Who must have sent the message (peer)
                hash=0
            ))
        return result

    def is_private(self, channel):
        with self._client as client:
            result = client.get_entity(channel).restricted
        return result # Boolean

    # InputPeerChannel(channel_id=1000910549, access_hash=5858828414308925479)
    # api.search_query(InputPeerChannel(channel_id=1444228991, access_hash=8253775144644352419), 'jesus')
    # api.get_channel_info(1444228991)['full_chat']['chat_photo']['access_hash']
    # print(api.search_query(1444228991, 'corona').count)
    # api.search_query(1444228991, ['corona', 'covid'])

#     >>> with api._client as client:
# ...     print(client.get_entity(1444228991).restricted)