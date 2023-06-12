import numpy as np
import tensorflow as tf
from transformers import DistilBertTokenizerFast, TFDistilBertForSequenceClassification

class UrgModel:
    """
    A class for performing inference with the URG model, a DistilBERT-based model for sequence classification.

    Args:
        model_path (str): The path to the pre-trained DistilBERT model.
        tokenizer_path (str): The path to the pre-trained DistilBERT tokenizer.
        weights_path (str): The path to the trained weights for the URG model.
        GPU (bool): A boolean that indicates whether to use GPU for inference

    Attributes:
        model: The TensorFlow model for the URG model.
        tokenizer: The tokenizer for the URG model.
        optimizer: The optimizer used to train the URG model.
    """
    def __init__(self, model_path = 'distilbert-base-uncased', tokenizer_path = 'distilbert-base-uncased', weights_path = 'urg_model_weights.h5', GPU = True):
        self.model = TFDistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.load_weights(weights_path)
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(tokenizer_path)
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5)
        self.model.compile(optimizer=self.optimizer,
                           loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                           metrics=['accuracy'])
        self.GPU = GPU
        

    def predict(self, tweet_text, batch_size=90):
        """
        Predicts the label of a given text string.

        Args:
            tweet_text (str): The text string to classify.
            batch_size (int): The batch size to use for predictions.

        Returns:
            np.array: An array of predicted labels for the list of tweets.
        """
        # if cpu is used for inference
        if not self.GPU:
            tf.config.set_visible_devices([], 'GPU')


        # Encoding Data
        real_data_encodings = self.tokenizer(tweet_text, truncation=True, padding=True)
        # Converting Data to a Huggingface Dataset object
        dataset = tf.data.Dataset.from_tensor_slices(dict(real_data_encodings))
        # Prediction
        predictions = self.model.predict(dataset.batch(batch_size))
        predicted_labels = np.argmax(predictions.to_tuple()[0], axis=1)
        return predicted_labels

if __name__ == '__main__':
    model = UrgModel()
    test_tweet = ['People are having fun in Hawaii', 'Fire are shots in a close neighborhood']
    predicted_labels = model.predict(test_tweet)
    print(predicted_labels)

