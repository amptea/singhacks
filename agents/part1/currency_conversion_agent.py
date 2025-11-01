from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=key)

def prompt_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        # Simply use the compound model ID
        model="groq/compound", 
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    print(prompt_groq(prompt))