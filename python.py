
import os
import torch
import whisper
from transformers import BartTokenizer, BartForConditionalGeneration

# Set cache path before loading models
CACHE_DIR = "C:/Users/Ashwini/Desktop/VideoSummaryCache"
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load and cache Whisper
print("Downloading Whisper model...")
whisper.load_model("base").to(device)

# Load and cache BART model
print("Downloading BART model...")
BartTokenizer.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR)
BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR).to(device)

print("✅ Models downloaded and cached successfully!")
