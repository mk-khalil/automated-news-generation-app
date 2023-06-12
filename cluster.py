import os
import re
import time
from bertopic import BERTopic
from bertopic.vectorizers import OnlineCountVectorizer, ClassTfidfTransformer
from river import stream, cluster
from umap import UMAP
from datetime import datetime


class RiverCluster:
    def __init__(self, model):
        """
        Initialize the RiverCluster class.

        Args:
            model: A clustering model from the river library.
        """
        self.model = model

    def partial_fit(self, umap_embeddings):
        """
        Partially fit the clustering model with UMAP embeddings.

        Args:
            umap_embeddings: UMAP embeddings of the data.

        Returns:
            self: The updated instance of the RiverCluster class.
        """
        for umap_embedding, _ in stream.iter_array(umap_embeddings):
            self.model = self.model.learn_one(umap_embedding)

        labels = []
        for umap_embedding, _ in stream.iter_array(umap_embeddings):
            label = self.model.predict_one(umap_embedding)
            labels.append(label)

        self.labels_ = labels
        return self


class TopicModeling:
    def __init__(self, file_path):
        """
        Initialize the TopicModeling class.

        Args:
            file_path: The path to the file for saving the model.
        """
        self.file_path = file_path

    def clean_text(self, text):
        """
        Clean the text by removing URLs, mentions, and hashtags.

        Args:
            text: The input text.

        Returns:
            The cleaned text.
        """
        text = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
        text = re.sub("@[A-Za-z0-9_]+", "", text)
        text = re.sub("#[A-Za-z0-9_]+", "", text)
        return text

    def save_model(self):
        """
        Save the topic modeling model.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class BERTopicModel(TopicModeling):
    def __init__(self, file_path):
        super().__init__(file_path)

        if os.path.isfile(file_path):
            self.model = BERTopic.load(file_path)
            print ('Clustering model loaded from file.')
        else:
            cluster_model = RiverCluster(cluster.DBSTREAM(fading_factor = 0.05))
            vectorizer_model = OnlineCountVectorizer(stop_words="english")
            ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True, bm25_weighting=True)

            self.model = BERTopic(
                hdbscan_model=cluster_model,
                vectorizer_model=vectorizer_model,
                ctfidf_model=ctfidf_model,
                language='english',
                nr_topics='auto',
                verbose=True
            )
            print ('Clustering model initialized.')

    def online_topic_modeling(self, tweet_dict):
        """
        Perform online topic modeling on a dictionary of tweets.

        Args:
            tweet_dict: A list of dictionaries containing tweet information.

        Returns:
            A tuple containing the updated tweet dictionary with assigned topic labels and a dictionary of topic statistics.
        """
        textlist = [self.clean_text(d['text']) for d in tweet_dict]
        self.model.partial_fit(textlist)

        topic_keywords = {k: v.split('_')[1:] for k, v in self.model.topic_labels_.items()}
        freq_df = self.model.get_topic_freq().loc[self.model.get_topic_freq().Topic != -1, :]
        topics = sorted(freq_df.Topic.to_list())
        all_topics = sorted(list(self.model.get_topics().keys()))
        indices = [all_topics.index(topic) for topic in topics]

        embeddings = [self.model.topic_embeddings_[i] for i in indices]
        embeddings = UMAP(n_neighbors=2, n_components=2, metric='cosine', random_state=42).fit_transform(embeddings)
        topic_coordinates = {i: embeddings[i].tolist() for i in indices}

        topic_sizes = dict(sorted(self.model.topic_sizes_.items()))

        #current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        current_time = datetime.utcnow()

        topic_list = [{'topic_label': key, 'size': topic_sizes[key], 'coordinates': topic_coordinates[key], 'keywords': topic_keywords[key]} for key in topic_keywords]
        topic_stats = {'time': current_time, 'topics': topic_list}

        for d in tweet_dict:
            d.pop('text', None)

        for d, value in zip(tweet_dict, self.model.topics_):
            d['topic_label'] = value

        return tweet_dict, topic_stats

    def save_model(self):
        """
        Save the BERTopic model.
        """
        self.model.save(self.file_path)
