import google.generativeai as genai
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables d’environnement à partir du fichier .env
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_embedding(text):
    result = genai.embed_content(
        model="text-embedding-004",
        content=text
    )
    return np.array(result["embedding"]) 
