import os
from gpt4all import GPT4All
from .models import db, LLMModel

# --- Configuration ---
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# --- In-memory cache for loaded GPT4All model instance ---
# A simple cache to hold one model at a time to manage memory.
model_cache = {
    "model_id": None,
    "model_instance": None,
}

def list_local_models():
    """Lists all models available in the local database."""
    return LLMModel.query.all()

def download_model(filename: str, model_name: str):
    """
    Downloads a GPT4All model, saves it locally,
    and adds its metadata to the database.
    """
    if LLMModel.query.filter_by(filename=filename).first():
        raise ValueError(f"Model '{filename}' is already downloaded.")

    print(f"Downloading GPT4All model: {filename}...")
    try:
        path = GPT4All.download_model(model_filename=filename, model_path=MODELS_DIR)
    except Exception as e:
        raise IOError(f"Failed to download model '{filename}': {e}") from e

    new_model = LLMModel(
        name=model_name or filename, # Use provided name or filename
        filename=filename,
        path=path
    )
    db.session.add(new_model)
    db.session.commit()

    return new_model

def get_model_instance(model_id: int):
    """
    Loads a GPT4All model instance into the cache if not already loaded.
    Returns the GPT4All model instance.
    """
    if model_cache["model_id"] == model_id and model_cache["model_instance"] is not None:
        print(f"Model {model_id} is already loaded in cache.")
        return model_cache["model_instance"]

    # Clear the cache if a different model is requested
    if model_cache["model_instance"] is not None:
        print(f"Clearing model {model_cache['model_id']} from cache.")
        # GPT4All objects don't have an explicit close method, so we just dereference
        model_cache["model_instance"] = None

    model_record = LLMModel.query.get(model_id)
    if not model_record:
        raise ValueError(f"Model with ID {model_id} not found in the database.")

    print(f"Loading GPT4All model '{model_record.name}' into memory...")
    try:
        model_instance = GPT4All(model_name=model_record.filename, model_path=MODELS_DIR)

        # Update the cache
        model_cache["model_id"] = model_id
        model_cache["model_instance"] = model_instance

        print(f"Model '{model_record.name}' loaded successfully.")
        return model_instance
    except Exception as e:
        raise RuntimeError(f"Failed to load model {model_record.name}: {e}") from e

def generate_text(model_id: int, prompt: str, max_tokens: int = 200):
    """Generates text using a specified GPT4All model."""
    model = get_model_instance(model_id)

    print(f"Generating text with model {model_id}...")
    try:
        with model.chat_session():
            response = model.generate(prompt=prompt, max_tokens=max_tokens)
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to generate text with model {model_id}: {e}") from e
