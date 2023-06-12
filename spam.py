import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class SpamDetector:
    def __init__(self, model_name = "johnpaulbin/autotrain-spam-39547103148", spam_threshold=0.75):
        """
        Initialize the SpamDetector with a specified model and tokenizer from Hugging Face.

        Args:
            model_name (str): The name of the Hugging Face model to load.
            spam_threshold (float, optional): The threshold probability for classifying a tweet as spam.
                Defaults to 0.8.
        """
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.spam_threshold = spam_threshold

    def classify_spam(self, text):
        """
        Classify a single piece of text as spam or not spam.

        Args:
            text (str): The text to classify.

        Returns:
            int: 1 if the text is classified as spam and 0 otherwise.
        """
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=-1).detach().numpy()
        label = probabilities.argmax(axis=-1)[0]
        score = probabilities.max(axis=-1)[0]

        if label == 1 and score >= self.spam_threshold:
            return 1  # Spam
        else:
            return 0  # Not spam

    def detect_spam(self, tweets_textlist):
        """
        Detect spam in a list of text using the specified Hugging Face model and tokenizer.

        Args:
            tweets_textlist (list): A list of strings containing the text to be classified.

        Returns:
            list: A list of integers (0 or 1) indicating whether each piece of text is spam (1) or not (0).
        """
        result = [self.classify_spam(tweet) for tweet in tweets_textlist]
        return result

if __name__ == "__main__":
    model_name = "johnpaulbin/autotrain-spam-39547103148"
    spam_detector = SpamDetector(model_name, spam_threshold=0.75)

    test_tweets = [
        "Breaking: Scientists discover a revolutionary weight loss method. Read more: tinyurl.com/weightlossnews 🥗 #HealthNews",
        "Shocking report reveals the secret to increasing your website traffic. Learn more: bit.ly/WebTrafficNews 🌐 #TechNews"
    ]

    spam_predictions = spam_detector.detect_spam(test_tweets)

    for tweet, prediction in zip(test_tweets, spam_predictions):
        print(f"Tweet: {tweet}\nPrediction: {'Spam' if prediction == 1 else 'Not Spam'}\n")