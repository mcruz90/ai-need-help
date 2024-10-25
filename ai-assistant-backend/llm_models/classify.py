from llm_models.classify_examples import examples
from config.config import cohere_client, Config

#TODO: Consider other types of classification. Perhaps for the router to improve on agent selection?
class Classifier:
    def __init__(self):
        self.client = cohere_client
        self.model = Config.CLASSIFY_MODEL

    def classify(self, query: str, examples: list) -> float:
        response = self.client.classify(
            model=self.model,
            inputs=[query],
            examples=examples
        )
        return response.classifications[0]

    def classify_time_sensitivity(self, query: str) -> float:
        classification = self.classify(query, examples)
        
        # Check if 'time_sensitive' is in the labels
        if 'time_sensitive' in classification.labels:
            return classification.labels['time_sensitive'].confidence
        else:
            # If 'time_sensitive' is not a label, assume it's the opposite of 'timeless'
            return 1 - classification.labels['timeless'].confidence


    #TODO: Add more examples to help with classifying query examples best routed to the tutor agent
    def classify_tutor_examples(self, query: str, tutor_examples: list) -> float:
        classification = self.classify(query, tutor_examples)
        return classification.labels.get('spam', 0).confidence
    
    #TODO: Add more examples to help with classifying query examples best routed to the calendar agent
    def classify_calendar_examples(self, query: str, calendar_examples: list) -> float:
        classification = self.classify(query, calendar_examples)
        return classification.labels.get('spam', 0).confidence
    
    #TODO: Add more examples to help with classifying query examples best routed to the web search agent
    def classify_web_search_examples(self, query: str, web_search_examples: list) -> float:
        classification = self.classify(query, web_search_examples)
        return classification.labels.get('spam', 0).confidence
    
    #TODO: Add more examples to help with classifying query examples best routed to the code agent
    def classify_code_examples(self, query: str, code_examples: list) -> float:
        classification = self.classify(query, code_examples)
        return classification.labels.get('spam', 0).confidence


classify_model = Classifier()