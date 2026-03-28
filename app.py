import os
from flask import Flask, request, jsonify, render_template
from summary_module import summarize_video, summarize_youtube
from quiz_module import generate_quiz, submit_quiz
from flask_cors import CORS
from translation_module import translate_summary

# Set model cache directory to an absolute path to prevent repeated downloads
CACHE_DIR = "C:/Users/Ashwini/Desktop/VideoSummaryCache"
os.environ["HF_HOME"] = CACHE_DIR
os.environ["WHISPER_MODELS_DIR"] = CACHE_DIR  # Ensures Whisper files are stored correctly

UPLOAD_FOLDER = "uploads"
SUMMARY_FILE = "generated_summary.txt"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, supports_credentials=True)

@app.route("/")
def home():
    return render_template("Home.html")

@app.route("/generate-summary", methods=["POST"])
def generate_summary():
    try:
        if os.path.exists(SUMMARY_FILE):
            os.remove(SUMMARY_FILE)

        if "videoFile" in request.files:
            video = request.files["videoFile"]
            if not video.filename:
                return jsonify({"error": "No video file provided"}), 400

            video_path = os.path.join(UPLOAD_FOLDER, video.filename)
            video.save(video_path)
            summary = summarize_video(video_path)
            os.remove(video_path)

        elif "youtubeLink" in request.form:
            youtube_url = request.form["youtubeLink"].strip()
            if not youtube_url:
                return jsonify({"error": "No YouTube link provided"}), 400
            
            print(f"Processing YouTube Link: {youtube_url}")
            summary = summarize_youtube(youtube_url)

        else:
            return jsonify({"error": "Invalid request format"}), 400

        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            f.write(summary)

        return jsonify({"summary": summary})
    except Exception as e:
        import traceback
        print("----- Exception Trace -----")
        traceback.print_exc()
        print("---------------------------")
        return jsonify({"error": str(e)}), 500


@app.route("/generate-quiz", methods=["POST"])
def generate_quiz_endpoint():
    try:
        data = request.get_json()  # Extract JSON input
        summary = data.get("summary", "").strip()  # Validate the summary
        
        if not summary:
            print("Error: No summary provided.") 
            return jsonify({"error": "No summary provided."}), 400

        # Call the `generate_quiz` function
        quiz_response = generate_quiz(summary)
        print("Debug: Quiz response:", quiz_response)  # Log the quiz response

        # Check for errors in the quiz response
        if "error" in quiz_response:
            error_message = quiz_response["error"]
            print("Error in quiz generation:", error_message)  # Debugging info
            return jsonify({"error": error_message}), 400
        
        # Return the quiz if successfully generated
        return jsonify(quiz_response)
    except Exception as e:
        print("Exception during quiz generation:", str(e))  # Debugging info
        return jsonify({"error": str(e)}), 500


@app.route("/submit-quiz", methods=["POST"])
def submit_quiz_endpoint():
    try:
        user_answers = request.json.get("answers", {})
        result = submit_quiz(user_answers)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/translate-summary", methods=["POST"])
def translate_summary_route():
    try:
        data = request.get_json()
        summary = data.get("summary", "").strip()
        target_lang = data.get("language", "").strip()

        if not summary or not target_lang:
            return jsonify({"error": "Missing summary or target language"}), 400

        translated = translate_summary(summary, target_lang)
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
