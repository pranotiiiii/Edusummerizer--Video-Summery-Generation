import os
import subprocess
import torch
import whisper
from transformers import BartTokenizer, BartForConditionalGeneration

# Set model cache directory
CACHE_DIR = "C:/Users/Ashwini/Desktop/VideoSummaryCache"
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR
os.environ["WHISPER_MODELS_DIR"] = CACHE_DIR

# ✅ Ensure required libraries are installed
required_libraries = ["torch", "transformers", "openai-whisper"]
for lib in required_libraries:
    try:
        __import__(lib)
    except ImportError:
        print(f"🔹 Installing missing package: {lib}")
        subprocess.run(["pip", "install", lib], check=True)

# ✅ Detect GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Using device: {device}")

# ✅ Function to check if model exists
def model_exists(model_name):
    """Checks if a model is already downloaded in the cache directory."""
    model_path = os.path.join(CACHE_DIR, f"models--{model_name}")
    return os.path.exists(model_path)

# ✅ Download Whisper model if missing
if not model_exists("openai--whisper-base"):
    print("⬇️ Downloading Whisper model...")
    whisper.load_model("base", download_root=CACHE_DIR).to(device)
else:
    print("✅ Whisper model already exists.")

# ✅ Download BART model if missing
if not model_exists("facebook--bart-large-cnn"):
    print("⬇️ Downloading BART model...")
    BartTokenizer.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR)
    BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR).to(device)
else:
    print("✅ BART model already exists.")

print("✅ All models are downloaded and ready!")
