from openai import OpenAI
import yaml
import os

class GenerateReport:
    """Analyzes sentiment using OpenAI's GPT model."""

    def __init__(self, config_path: str = None):
        """Initialize the OpenAI API client with settings from config/settings.yaml."""
        if config_path is None:

            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        
        config_path = os.path.abspath(config_path)

        with open(config_path, 'r') as file:
            settings = yaml.safe_load(file)

        os.environ["OPENAI_API_KEY"] = settings['openai']['api_key']
        self.client = OpenAI()
        self.model_name = settings['openai']['model_name']
        self.prompt_template = (
            "You are a financial analyst. Make a report of few sentences for the stock ticker {ticker}. "
            "The sentiment score is {sentiment_score}, the final signal computed by the strategy is '{final_signal}' and the confidence level is'{confidence}'."
            "Our analysis suggests that {explanation}. "
        )

    def generate_report(self, ticker=str, sentiment_score=str, final_signal=str, confidence=str, explanation=str):

        prompt = self.prompt_template.format(ticker=ticker, sentiment_score=sentiment_score, final_signal=final_signal, confidence=confidence, explanation=explanation)

        response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=150,
                    )

        return response.choices[0].message.content.strip()
