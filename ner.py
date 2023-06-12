from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline


class NamedEntityRecognizer:
    def __init__(self, model_name_or_path="dslim/bert-base-NER", aggregation_strategy="max"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name_or_path)
        self.nlp = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy=aggregation_strategy)
        
    def predict(self, text):
        results = self.nlp(text)
        tweets_ents = []
        for res in results:
            entities = {'Person':[], 'Location':[], 'Org':[]}
            for entity in res:
                if entity['entity_group'] == 'PER':
                    entities['Person'].append(entity['word'])

                elif entity['entity_group'] == 'LOC':
                    entities['Location'].append(entity['word'])

                elif entity['entity_group'] == 'ORG':
                    entities['Org'].append(entity['word'])

            tweets_ents.append(entities)
        return tweets_ents
    
if __name__ == '__main__':
    ner = NamedEntityRecognizer()
    example = ["My name is Wolfgang and I live in Berlin", "President Joe and Ligma visits Ohio", "A huge fire takes place in Alexandria, Egypt"]

    print(ner.predict(example))