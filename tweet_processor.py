import argparse
import time
from pymongo import MongoClient
from utils import urg_ner_spam
from twitter_mongoDB.load_database import populate_database


class TwitterStreamProcessor:
    """
    A class for streaming and processing tweets from Twitter's Streaming API.

    Args:
        keyword_list (list): A list of keywords to filter tweets by.
        total_number (int): The total number of tweets to stream.
        batch_size (int, optional): The number of tweets to stream and process at a time. Defaults to 2.
    """

    def __init__(self, keyword_list, total_number, batch_size=2):
        self.keyword_list = keyword_list
        self.total_number = total_number
        self.batch_size = batch_size
        self.client = MongoClient()
        self.db = self.client["twitter_data"]
        self.tweet_buffer = self.db["tweet_buffer"]
        self.tweet_filtered = self.db["tweet_filtered"]

    def stream_tweets(self):
        """Stream tweets from Twitter's Streaming API and store them in the tweet_buffer collection."""
        populate_database(self.batch_size, self.total_number, self.keyword_list)
        
    def process_tweets(self):
        """
        Extract all data from the tweet_buffer collection, apply data processing and predictions
        using the urg_ner function, and store the filtered buffer into the tweet_filtered collection.
        """
        # extract all data from the tweet_buffer collection
        buffer_data = list(self.tweet_buffer.find({}))
        print ('Size of buffer data = ', len(buffer_data))

        # apply data processing and predictions using your function
        if buffer_data:
            filtered_buffer = urg_ner_spam(buffer_data)
            print('Size of filtered data= ', len(filtered_buffer))

            
            for d in filtered_buffer:
                # delete the previous document id
                del d['_id']
            if filtered_buffer:
                # store the filtered buffer into the tweet_filtered collection
                self.tweet_filtered.insert_many(filtered_buffer)

        # clear all data in the tweet_buffer collection
        self.tweet_buffer.delete_many({})

    def run(self):
        """Run the main loop that streams and processes tweets."""
        while True:
            print(f"\nLoading tweets about {self.keyword_list} into database...\
                  \nWait for progress status...\n\n")
            self.stream_tweets()
            self.process_tweets()
            time.sleep(60)  # wait 60 seconds before streaming and processing more tweets


if __name__ == '__main__':
    # define command line arguments
    parser = argparse.ArgumentParser(description='Stream and process tweets from Twitter\'s Streaming API.')
    parser.add_argument("-k", "--keywords", nargs="+", help="list of keywords for filtering tweets", required=True)
    parser.add_argument("-n", "--num_tweets", type=int, help="number of tweets to stream at a time", required=True)
    parser.add_argument('-b', '--batch_size', type=int, help='How many tweets do you want to grab at a time?', default=2)
    args = parser.parse_args()
    
    stream_processor = TwitterStreamProcessor(args.keywords, args.num_tweets, args.batch_size)
    
    while True:
        stream_processor.run()