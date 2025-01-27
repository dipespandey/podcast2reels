import nltk

from youtube_utils import download_youtube_video, get_transcript
from gpt_utils import (
    create_single_string_from_transcript,
    ask_openai_for_topic_segments,
    parse_gpt_segments
)
from video_processor import cut_video_with_subtitles


def main(youtube_url, vertical=False):
    """
    Main function to process a YouTube video into topic-segmented reels.
    """
    print("[STEP] Downloading the YouTube video...")
    video_file = download_youtube_video(youtube_url, "original_video.mp4")
    if not video_file:
        print("[ERROR] Could not download. Exiting.")
        return

    print("[STEP] Fetching transcript from YouTube...")
    transcript_data = get_transcript(youtube_url)
    if not transcript_data:
        print("[ERROR] Transcript not found. Exiting.")
        return

    print(f"[INFO] Transcript has {len(transcript_data)} lines.")
    transcript_str = create_single_string_from_transcript(transcript_data)

    print("[STEP] Asking OpenAI to produce topic segments with start/end from the transcript.")
    gpt_segments = ask_openai_for_topic_segments(transcript_str)
    if not gpt_segments:
        print("[ERROR] GPT did not return a valid segment list. Exiting.")
        return

    segments = parse_gpt_segments(gpt_segments)
    print(f"[INFO] GPT returned {len(segments)} segments.")

    print("[STEP] Cutting the video into topic segments with 'TikTokFunky' subtitles.")
    cut_video_with_subtitles(
        video_file,
        segments,
        transcript_data,
        output_folder="topic_segments",
        vertical=vertical,
    )

    print("[DONE] Check the 'topic_segments' folder for your final funky subtitled clips.")


if __name__ == "__main__":
    # Example usage:
    TEST_URL = "https://www.youtube.com/watch?v=Ff4fRgnuFgQ"
    nltk.download('punkt')  # Ensure NLTK data is available
    main(TEST_URL, vertical=True)
