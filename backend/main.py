import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    model: str
    prompt: str

class CodeRequest(BaseModel):
    prompt: str
    model: str

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

@app.get("/")
def read_root():
    return {"message": "AI Toolkit Backend is running!"}

@app.get("/api/v1/models")
def get_models():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        response.raise_for_status()  # Raise an exception for bad status codes
        models_data = response.json().get("models", [])
        # Extract just the model names (e.g., "llama2:latest")
        model_names = [model["name"] for model in models_data]
        return {"models": model_names}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Ollama. Make sure Ollama is running."}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while fetching models from Ollama: {e}"}

@app.post("/api/v1/chat")
def chat(chat_request: ChatRequest):
    try:
        payload = {
            "model": chat_request.model,
            "prompt": chat_request.prompt,
            "stream": False  # For simplicity, we'll use non-streaming responses for now
        }
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Ollama. Make sure Ollama is running."}
    except requests.exceptions.RequestException as e:
        # Handle cases where the model might not exist on Ollama
        if e.response and e.response.status_code == 404:
            return {"error": f"Model '{chat_request.model}' not found on Ollama."}
        return {"error": f"An error occurred while communicating with Ollama: {e}"}

@app.post("/api/v1/generate/code")
def generate_code(code_request: CodeRequest):
    try:
        # This prompt is designed to coax the model into generating a single, clean HTML file.
        full_prompt = f"""
        Task: Generate a complete, single HTML file based on the following request.
        Request: "{code_request.prompt}"

        Constraints:
        - The entire output must be a single HTML file.
        - All CSS and JavaScript must be embedded directly within the HTML file in <style> and <script> tags.
        - Do NOT include any explanations, comments, or markdown formatting (like ```html) outside of the HTML structure.
        - The code should be functional and self-contained.

        Begin output now:
        """

        payload = {
            "model": code_request.model,
            "prompt": full_prompt,
            "stream": False
        }
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        response.raise_for_status()

        generated_code = response.json().get("response", "").strip()

        # Clean up the response if the model still includes markdown fences
        if generated_code.startswith("```html"):
            generated_code = generated_code[7:]
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]

        return {"code": generated_code.strip()}

    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Ollama. Make sure Ollama is running."}
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            return {"error": f"Model '{code_request.model}' not found on Ollama."}
        return {"error": f"An error occurred while communicating with Ollama: {e}"}
