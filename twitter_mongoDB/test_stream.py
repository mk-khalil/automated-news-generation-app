import config
import tweepy 


#auth = OAuthHandler(config.CONSUMER_API_KEY, config.CONSUMER_API_SECRET)
#auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)

#print (auth)
#LOCAL_DB = config.LOCAL_CLIENT.twitter_data
#LOCAL_DB.tweet_dicts.insert_one({'tweet':'first_tweet'})
auth = tweepy.OAuth2BearerHandler(config.BEARER_TOKEN)
api = tweepy.API(auth)

search_terms = ['kanye', 'war']

class KStream (tweepy.StreamingClient):
    def on_connect(self):
        print ('Connected')
        return super().on_connect()
    

stream = KStream(bearer_token=config.BEARER_TOKEN)
