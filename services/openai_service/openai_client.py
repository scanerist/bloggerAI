import openai
from services.shared.config import Config

openai.api_key = Config.OPENAI_API_KEY

class OpenAIService:
    @staticmethod
    async def modify_post(content: str, instruction: str) -> str:
        prompt = f"{instruction}\n\n{content}"
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
