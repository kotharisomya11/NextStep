from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Gemini API key was not found.")
    exit()

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-flash-lite-latest",
    contents="Say hello in one simple sentence."
)

print("Response:")
print(response.text)