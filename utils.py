import operator
from ner import NamedEntityRecognizer
from urgency_detection import UrgModel
from spam import SpamDetector

def urg_ner_spam(tweet_batch):
    # A function for applying urgency detection and named entity recognition to a batch of tweets.
    
    if tweet_batch == None:
        return None
    
    # extracting text from tweet dictionaries
    batch_text = list(map(operator.itemgetter('text'), tweet_batch))

    # urgency detection
    urg_model = UrgModel()
    predicted_labels = urg_model.predict(batch_text)
    # convert labels to list of integers instead of numpy array
    predicted_labels = predicted_labels.astype(int).tolist()
    # tweets after applying urgency detection model
    tweets_urgency = list(map(lambda s, urg: {**s, 'urgent': urg}, tweet_batch, predicted_labels))

    # filtering out the un-urgent (uninformative tweets)
    filtered_tweets = [d for d in tweets_urgency if d.get('urgent') == 1]

    # if all tweets are filtered return none
    if filtered_tweets == []:
        return None
    
    # spam detection
    filtered_tweets_text = list(map(operator.itemgetter('text'), filtered_tweets))

    spam_detector = SpamDetector(spam_threshold=0.75)

    spam_predictions = spam_detector.detect_spam(filtered_tweets_text)


    # tweets after applying spam detection
    tweets_spam = list(map(lambda s, spam: {**s, 'spam': spam}, filtered_tweets, spam_predictions))
    filtered_tweets = [d for d in tweets_spam if d.get('spam') == 0]

    # if all tweets are filtered return none
    if filtered_tweets == []:
        return None
    
    
    # named entity recongnition for the filtered tweets
    ner = NamedEntityRecognizer()
    # extracting text of filtered tweets
    batch_filtered = list(map(operator.itemgetter('text'), filtered_tweets))
    # prediction
    tweets_ner = ner.predict(batch_filtered)

    # tweets after applying ner
    tweets_dict = list(map(lambda s, ner: {**s, 'ner': ner}, filtered_tweets, tweets_ner))

    return (tweets_dict)

