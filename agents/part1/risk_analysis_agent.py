import groq as groq
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("API_KEY")

client = groq.Client(api_key=key)

def chat(prompt):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[ # list of dictionaries
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

# let me input my prompt into the terminal upon running the script
if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    response = chat(prompt)
    print(f"Response from the model: {response}")

