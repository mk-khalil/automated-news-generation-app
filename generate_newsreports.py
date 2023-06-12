import time
import re
import poe
from datetime import datetime
import pytz
from pymongo import MongoClient
from classification_zeroshot import NewsClassifier

class NewsReportGenerator:
    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client["twitter_data"]
        self.tweet_filtered = self.db["tweet_filtered"]
        self.topic_status_change = self.db['topic_status_change']
        self.news_report = self.db['news_report']

    @staticmethod
    def clean_tweets(tweet):
        # Remove URLs
        tweet = re.sub(r"http\S+|www\S+|https\S+", '', tweet, flags=re.MULTILINE)
        
        # Remove special characters and numbers
        #tweet = re.sub(r'\W+|\d+', ' ', tweet)
        
        # Remove emojis
        tweet = tweet.encode('ascii', 'ignore').decode('ascii')
        
        # Convert to lowercase
        tweet = tweet.lower()
        return tweet
    
    @staticmethod
    def extract_title(md_string):
        # Regular expression to match Markdown title patterns
        title_pattern = r"^(?:\#{1,6}|\*{1,3}|\_{1,3})\s+(.+)$"
        lines = md_string.split("\n")

        for line in lines:
            match = re.match(title_pattern, line)
            if match:
                return match.group(1)

        # Return None if no title is found
        return None

    @staticmethod
    def parse_datetime(datetime_str):
        # a function to parse the datetime string from the tweet
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
    
    def get_api_response(self, tweets):
        # a function to get the api response from the poe api
        poe_client = poe.Client("q2LaYYHAtN6LjLG1vwxGzw%3D%3D")

        #intro = 'Please generate a comprehensive news report based on the provided tweets. Deduce the common theme or event described in the tweets and provide a descriptive title for the report. Include relevant information from each tweet, establish connections between the tweets, and provide a cohesive narrative of the news event. Pay attention to key details such as the location, time, impact, and any additional information that would be relevant to the news report. Ensure that the generated report is clear, concise, and captures the essence of the tweets in a coherent manner.'
        #outro = 'Ensure the news report includes an introduction, background, key developments, reactions and responses, and a conclusion.'
        intro = 'Generate a comprehensive news report based on the following tweets, focusing on the common theme or event they describe. Provide a descriptive title for the report, and include relevant information from each tweet, establishing connections between them to create a cohesive narrative. Your news report should cover key details such as location, time, impact, and any additional relevant information, and be organized into sections such as an introduction, background, key developments, reactions and responses, and a conclusion with proper markdown format. Ensure the report is clear, concise, and captures the essence of the tweets in a coherent manner. Do not reference the tweets in your report..\n'
        
        formatted_tweets = ''
        for index, tweet in enumerate(tweets):
            formatted_tweets += f"Tweet {index}: {tweet}\n"
        
        prompt = '\n'.join([intro, formatted_tweets])

        for chunk in poe_client.send_message("beaver", prompt, with_chat_break = True, timeout = 120):
            pass
        return chunk['text']
    
    def gen_topic_report(self, topic_label, topic_status):
        # a function to generate a news report for a certian cluster topic     
        matching_documents = self.tweet_filtered.find({"topic_label": topic_label})
        cleaned_tweets = []
        tweet_dates = []
        for tweet in matching_documents:
            tweet_text = tweet['text']
            cleaned_tweet = self.clean_tweets(tweet_text)
            cleaned_tweets.append(cleaned_tweet)

            #tweet_dates.append(self.parse_datetime(tweet['tweet_created_at'] ))
            tweet_dates.append(tweet['tweet_created_at'] )


        size = topic_status['size']
        
        created_at = datetime.utcnow()
        
        topic_recent_date = max(tweet_dates)
        topic_oldest_date = min(tweet_dates)

        summary = self.get_api_response(cleaned_tweets)
        title = self.extract_title(summary)

        # classify news summary category
        news_category = NewsClassifier(task = 'news_category')
        cat_output = news_category.classify([summary])
        categories = news_category.process_output(cat_output)[0]

        # classify news summary priority
        news_priority = NewsClassifier(task = 'news_priority')
        prior_output = news_priority.classify([summary])
        priority = news_priority.process_output(prior_output)[0]

        topic_report = { 'topic_label': topic_label,
                        'title': title, # title is the first line of the summary
                        'summary': summary,
                        'size': size,
                        'categories':categories,
                        'priority': priority,
                        'created_at': created_at,
                        'topic_recent_date': topic_recent_date, 'topic_oldest_date': topic_oldest_date}
        print(f'News report generated for topic: {topic_label}\n')
        return topic_report

    def run_report_generation(self):
        # Retieve the topic_labels and corresponding size and timestamps from the database
        status_docs = self.topic_status_change.find()
        status_array = []
        for doc in status_docs:
            topic_label = doc["topic_label"]
            size = doc["size"][-1]
            timestamp = doc["time"][-1]
            topic_status = {'topic_label': topic_label, 'size': size, 'timestamp': timestamp}
            status_array.append(topic_status)

        for topic_status in status_array:
            # check if the topic is already summarized
            topic_report = self.news_report.find_one({"topic_label": topic_status['topic_label']})

            if topic_report:
                # check if size increased by at least 10 new tweets
                if topic_report['size'] <= topic_status['size'] + 10:
                    continue
                else:
                    # generate new modified summary
                    topic_report = self.gen_topic_report(topic_status['topic_label'], topic_status)
                    insert_result = self.news_report.insert_one(topic_report)

            elif topic_status['size'] >= 10:
                # check if the cluster size is at least 10
                # generate new summary
                topic_report = self.gen_topic_report(topic_status['topic_label'], topic_status)
                insert_result = self.news_report.insert_one(topic_report)
            else: 
                continue
            print(f'Generated Summary for topic: {topic_status["topic_label"]}\n')
        return
    
    def main(self):
        self.run_report_generation()
        print('Reports Generation Done Successfully')


if __name__ == "__main__":
    generator = NewsReportGenerator()
    generator.main()