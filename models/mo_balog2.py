import math
import statistics
import numpy as np
import time
from tqdm import tqdm
from telethon.tl.types import InputPeerChannel

class Balog2:

    def __init__(self, telethon_api):
        self.telethon_api = telethon_api

    def rank(self, channels, query):
        ranked_channels = []

        for channel in tqdm(channels):
            prob_query_posts = 0 # P(q|post)
            for term in query:
                messages_object = self.telethon_api.search_query(channel, term)
                # Check if the term appears in the channel
                if messages_object.count == 0:
                    #print('Term', term, 'not found in channel', channel)
                    break
                # Get all the messages where the term of the query appears
                messages = messages_object.messages
                for m in messages:
                    # Transform the message string in a list of words
                    m_as_list = m.message.split()
                    num_t_post = 0
                    num_all_terms_post = len(m_as_list)
                    if num_all_terms_post == 0:
                        break
                    for word in m_as_list:
                        if term in word.lower():
                            num_t_post += 1
                    prob_query_posts += num_t_post/num_all_terms_post
            prob_query_channel = prob_query_posts #TODO: divide by total number of msgs in chat
            # Add channel with score
            ranked_channels.append([channel, prob_query_channel])
        # Sort so that highest ranking channels are on top
        ranked_channels.sort(reverse=True, key=lambda tup: tup[1])
        return ranked_channels
                        
    def get_filtered_channels(self, channels):
        num_channels = len(channels) if len(channels) else 1 # If there are no channels make it 1 to avoid division by zero
        avg_score = sum([ch[1] for ch in channels])/num_channels
        filtered_channels = [ch[0] for ch in channels if ch[1] > 0.5]
        return filtered_channels, avg_score