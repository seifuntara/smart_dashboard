import os
from dotenv import load_dotenv
from groq import Groq

# Load .env explicitly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# THIS is where GROQ_API_KEY is used
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_completion_tokens=300
    )
    return completion.choices[0].message.content

