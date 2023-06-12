"""
The purpose of this script is to intercept real-time, streamed tweets
using some of tweepy's built-in Classes:

    1. OAuthHandler
        - for authenticating API keys, tokens, etc.

    2. StreamingClient
        - to use as a template for creating a custom
          TwitterListener class, which decides how to parse each
          tweet (JSON string) as it is intercepted.

The keywords can be altered at the end of the script.

"""

import json
import tweepy
from . import config
from datetime import datetime


LANGUAGES = ['en']

def get_geo_data(tweet):

    geo_data = []
    if tweet['data']['geo'] != {}:
        try:
            geo_data.append(tweet['includes']['places'][0]['full_name'])
            geo_data.append(tweet['includes']['places'][0]['geo']['bbox'])
        except KeyError:
            geo_data.append(['KeyError'])

    return geo_data

def get_entities(tweet):
    '''Function that extracts the entities from each tweet directly
    from the context annotations for tweet
    '''
    entities = {}

    if 'context_annotations' in tweet['data'] and len(tweet['data']['context_annotations']) > 0:
        for c in tweet['data']['context_annotations']:
            if c['domain']['name'] in entities:
                entities[c['domain']['name']].append(c['entity']['name'])
            else: 
                entities[c['domain']['name']] = [c['entity']['name']]
    return entities

def get_hashtags(tweet):

    '''Function that extracts the hashtags from each tweet,
       which comes in as a JSON string.
    '''

    hashtags = []

    if 'hashtags' in tweet['data']['entities']: 
      if len(tweet['data']['entities']['hashtags']) > 0:
        for hashtag in tweet['data']['entities']['hashtags']:
          hashtags.append(hashtag['tag'])
    return hashtags
def get_data_object(tweet):

    '''Function that extracts the data object from each tweet,
       which comes in as a JSON string.
    '''

    date_string = tweet['data']['created_at']
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    date_object = datetime.strptime(date_string, date_format)

    return date_object
   
def get_tweet_dict(tweet):

    '''Function that extracts relevant information from the tweet
       (using the 3 user-defined functions from above) and structures the
       data into a dictionary -- in preparation for loading into MongoDB.
    '''
    # Extracting user name
    if tweet['includes']['users'][0]['id'] == tweet['data']['author_id']:
      username =  tweet['includes']['users'][0]['username']
    else:
      username = 'N/A'

    text = tweet['data']['text']

    geo_data = get_geo_data(tweet)
    entities = get_entities(tweet)
    hashtags = get_hashtags(tweet)
    date = get_data_object(tweet)
    tweet = {'id': tweet['data']['id'],
             'tweet_created_at': date,
             'text': text,
             'user': username,
             'language': tweet['data']['lang'],
             'followers_count': tweet['includes']['users'][0]['public_metrics']['followers_count'],
             'like_count': tweet['data']['public_metrics']['like_count'],
             'hashtags': hashtags,
             'tweet_location': geo_data,
             'entities': entities,
             }
    return tweet

class TwitterAuthenticator():

    """Class, whose sole purpose is to provide authentication to use
       the Twitter API.
    """
    def authenticate(self):
        """
        Use tweepy's built-in OAuthHandler class to return authentication object.
        """
        auth = tweepy.OAuth1UserHandler(config.CONSUMER_API_KEY, config.CONSUMER_API_SECRET, config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
        return auth

class TwitterListener(tweepy.StreamingClient):

    '''Required Class that inherits from tweepy.StreamingClient.
       The 'on_data()' method dictates what should be done with tweets
       as soon as they come in contact with the Listener stream.
    '''

    def __init__(self, limit, callback, langs, *args, **kwargs):
      super().__init__(*args, **kwargs)  # Inherit __init__ method from parent class.
      self.limit = limit
      self.counter = 0
      self.callback = callback
      self.langs = langs

    def on_connect(self):
        print ('Stream Connected')
    def on_disconnect(self):
       print ('Stream Disconnected')

    def on_data(self, data):

      '''DEFAULT method inherited from StreamListener class.

          This is the main function of the Twitter Streamer class.

          It defines what should be done with each incoming streamed tweet as it
          is intercepted by the StreamListener:

          - convert each json-like string from twitter into a workable JSON object;
          - ignore retweets, replies, and quoted tweets;
          - apply the get_tweet_dict function to each object;
          - apply a callback function to the resulting dictionary;
          - shut off StreamListener as soon as it reaches a pre-defined limit.
      '''
      t = json.loads(data)

      tweet_lang = t['data']['lang']
      # if tweet language is the same as requested or language specified 
      lang_flag = tweet_lang in self.langs or len(self.langs) == 0  

      # if tweet is original (not retweet or reply)
      tweet_org = not ('referenced_tweets' in t['data'] or 'in_reply_to_user_id' in t['data'])

      if lang_flag and tweet_org:
        
         tweet = get_tweet_dict(t)
         self.callback(tweet)

         self.counter += 1
         if self.counter == self.limit:
           print ('limit reached')
           self.disconnect()

class TwitterStreamer():
    '''
       Class containing the primary method / functionality of the script.
    '''

    def __init__(self, keywords):
        self.keywords = keywords
        self.twitter_authenticator = TwitterAuthenticator()

    def stream_tweets(self, limit, callback, langs):
        '''
            Primary function that wraps up all preceeding code into one method.
        '''

        stream = TwitterListener(bearer_token = config.BEARER_TOKEN, limit=limit, callback=callback, langs = langs)
        
        #TODO: keep the rules list constant 

        #detelting existing rules
        if (stream.get_rules().data):

            rules_to_delete = []

            for rule in stream.get_rules().data:
                if rule.value not in self.keywords:
                    rules_to_delete.append(rule.id)
                    print ('deleting rule: ', rule.value)

            if rules_to_delete:
                stream.delete_rules(rules_to_delete)



        for term in self.keywords:
            if term not in [rule.value for rule in stream.get_rules().data]:
                print('adding rule: ', term)
                stream.add_rules(tweepy.StreamRule(term))


        stream.filter(expansions=['geo.place_id', 'author_id'], \
                      tweet_fields = ['created_at','in_reply_to_user_id','referenced_tweets', 'lang', 'context_annotations','entities', 'public_metrics'],\
                        user_fields = ['description','public_metrics'], place_fields = ['geo'] )




if __name__ == "__main__":

    twitter_streamer = TwitterStreamer(['war'])
    twitter_streamer.stream_tweets(5, print)
