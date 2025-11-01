import groq as groq
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("API_KEY")
groq_base_url = os.getenv("GROQ_BASE_URL")
if not key:
    # Helpful, non-secret error when the key isn't present.
    raise RuntimeError(
        "Missing API key: set the API_KEY environment variable or add it to a local .env file.\n"
        "Do NOT commit your real key to the repository. For local PowerShell testing you can run: `$env:API_KEY=\"<your-key>\"`\n"
        "If you accidentally committed a key, rotate it and remove .env from git history.`"
    )

try:
    client = groq.Client(api_key=key)
except Exception as exc:
    # Wrap and surface the error with guidance (without printing the key)
    raise RuntimeError(
        "Failed to initialize GROQ client. Verify your API key and network connectivity."
    ) from exc

def chat(prompt):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[ # list of dictionaries
            {"role": "user", 
            "content": prompt}
            ]
    )
    return response.choices[0].message.content

# let me input my prompt into the terminal upon running the script
if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    response = chat(prompt)
    print(f"Response from the model: {response}")

