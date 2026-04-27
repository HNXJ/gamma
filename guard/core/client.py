from openai import OpenAI
from .config import Config

class GuardClient:
    def __init__(self, config: Config):
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        self.model = config.model

    def get_response(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error contacting model: {str(e)}"
