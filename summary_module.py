import os
import whisper
import ffmpeg
import yt_dlp
import torch
import uuid
import glob
import shutil  # ✅ Import shutil for file deletion
from transformers import BartTokenizer, BartForConditionalGeneration


# Set model cache directory
CACHE_DIR = "C:/Users/Ashwini/Desktop/VideoSummaryCache"
os.environ["HF_HOME"] = CACHE_DIR  # ✅ Updated from TRANSFORMERS_CACHE

# ✅ Define device properly
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Using device: {device}")  # Debugging info

# ✅ Load BART model & tokenizer BEFORE moving to GPU
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR)
summarizer = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn", cache_dir=CACHE_DIR).to(device)

# ✅ Load Whisper ASR model AFTER BART model
asr_model = whisper.load_model("base").to(device)

# Ensure directories exist
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# 🔹 Cleanup function to delete temporary files
def cleanup_files():
    """Deletes cached files and processed audio."""
    for file in glob.glob("audio_files/*.wav"):
        os.remove(file)  # ✅ Delete all audio files
    shutil.rmtree(CACHE_DIR, ignore_errors=True)  # ✅ Clear cache directory
    print("✅ Cache & Audio Files Deleted.")

def get_video_duration(path):
    """Returns video duration in seconds using ffmpeg."""
    try:
        probe = ffmpeg.probe(path)
        return float(probe['format']['duration'])
    except Exception as e:
        print(f"❌ Failed to get duration: {e}")
        return 0


# 🔹 Extract audio from video
def extract_audio(video_path):
    """Extracts audio from video with optimized settings."""
    audio_filename = f"audio_{uuid.uuid4().hex}.wav"
    audio_path = os.path.join(AUDIO_FOLDER, audio_filename)

    try:
        ffmpeg.input(video_path).output(audio_path, ar="16000", ac="1").run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        print(f"✅ Audio extracted successfully: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        return None

# 🔹 Transcribe audio to text
def transcribe_audio(audio_path):
    """Converts extracted audio into text using Whisper ASR."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise ValueError(f"❌ Invalid or empty audio file: {audio_path}")

    try:
        # ✅ Use FP16 only if CUDA is available, otherwise use FP32
        use_fp16 = torch.cuda.is_available()
        transcription = asr_model.transcribe(audio_path, language="en", fp16=use_fp16)
        return transcription["text"]
    except Exception as e:
        raise RuntimeError(f"❌ Error transcribing audio: {str(e)}")

# 🔹 Summarize transcribed text
def summarize_text(text, min_len=50, max_len=150):
    inputs = tokenizer(text, truncation=True, max_length=1024, return_tensors="pt").to(device)
    summary_ids = summarizer.generate(**inputs, max_length=max_len, min_length=min_len, do_sample=False)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

# 🔹 Process local video
def summarize_video(video_path):
    """Processes a locally uploaded video file to generate a summary."""
    print(f"🎬 Extracting audio from: {video_path} ...")
    audio_path = extract_audio(video_path)

    if audio_path:
        print(f"🗣️ Transcribing audio from: {audio_path} ...")
        try:
            text = transcribe_audio(audio_path)
            video_duration = get_video_duration(video_path)
            # Dynamic summary length
            if video_duration <= 300:
                min_len, max_len = 150, 300
            elif video_duration <= 600:
                min_len, max_len = 300, 500
            elif video_duration <= 900:
                min_len, max_len = 450, 700
            elif video_duration <= 1800:
                min_len, max_len = 600, 900
            elif video_duration <= 3600:
                min_len, max_len = 800, 1100
            else:
                min_len, max_len = 1000, 1300

            print("📝 Generating summary...")
            summary = summarize_text(text, min_len, max_len)
            cleanup_files()  # ✅ Delete temporary files after processing
            return summary
        except Exception as e:
            return f"❌ Error in processing video: {str(e)}"
    else:
        return "❌ Failed to extract audio."

# 🔹 Process YouTube video
def summarize_youtube(youtube_url):
    """Downloads audio from a YouTube video, transcribes it, and returns a summary."""
    unique_id = uuid.uuid4().hex
    output_template = os.path.join(AUDIO_FOLDER, f"youtube_{unique_id}.%(ext)s")

    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': output_template,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'noplaylist': True,
    'quiet': True,
    'verbose': True, 
    'cookies_from_browser': ('edge', {'profile': 'Default'})

    }

    audio_path = None  # Initialize audio_path to avoid reference errors
    try:
        os.makedirs(AUDIO_FOLDER, exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            print("✅ Download completed.")

        # Find the correct extracted audio file
        audio_files = glob.glob(os.path.join(AUDIO_FOLDER, f"youtube_{unique_id}.wav"))
        if not audio_files or not os.path.exists(audio_files[0]) or os.path.getsize(audio_files[0]) == 0:
            raise FileNotFoundError("❌ YouTube audio download failed - no valid audio file found.")


        audio_path = audio_files[0]  # Pick the first found WAV file
        print(f"🔍 Found downloaded file: {audio_path}")
        summary = summarize_video(audio_path)
        return summary
    except Exception as e:
        return f"❌ Error in processing YouTube video: {str(e)}"
    finally:
        # Clean up any downloaded audio files
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
