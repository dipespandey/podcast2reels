import json
import re
import openai
from openai.resources.chat.completions import ChatCompletion

from config import OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def create_single_string_from_transcript(transcript_data):
    """
    Convert each line in the transcript into: [start=XX.xx] text
    """
    lines = []
    for item in transcript_data:
        start = item["start"]
        text = item["text"].replace("\n", " ").strip()
        lines.append(f"[start={start}] {text}")
    return "\n".join(lines)

def ask_openai_for_topic_segments(transcript_str):
    """
    Calls GPT to produce a JSON array with {topic, start, end},
    where 'start' and 'end' come from the original transcript lines.
    """
    system_prompt = (
        "You are a helpful assistant that segments a YouTube transcript of an interview.\n"
        "- The interview has two people: an interviewer and a guest.\n"
        "- The interviewer typically starts with a question or new topic.\n"
        "- The transcript lines are provided, each in the format: [start=TIMESTAMP] TEXT.\n"
        "- Please group consecutive lines so that each segment starts with the interviewer's question.\n"
        "- Make sure you use good time windows for each timestamped text so that the segment doesn't end abruptly and always make sure two segments don't have overlapping ideas.\n"
        "- Also make sure the segments are not too short, at least 20 seconds long and not more than 1 minute 30 seconds.\n"
        "- Use the 'start' time of that question as 'start'.\n"
        "- Use the 'start' time of the next interviewer question as 'end' (or the last line's start if it's the final segment).\n"
        "- Return valid JSON only: an array of objects, each with:\n"
        "   { \"topic\": \"...\", \"start\": float, \"end\": float }\n"
        "- The 'topic' should be a short phrase describing the question or topic.\n"
        "- 'start' and 'end' must be from the existing [start=...] lines.\n"
        "- Do not add extra text outside the JSON.\n"
    )
    user_prompt = (
        "Here is the transcript with timestamps:\n\n"
        f"{transcript_str[:16000]}\n\n"
        "Please return only the JSON array as your answer."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.0,
        )
        return parse_openai_response(response)
    except Exception as e:
        print(f"[ERROR] OpenAI API Error: {e}")
        return None

def parse_openai_response(response: ChatCompletion):
    """
    Extract and parse JSON from the OpenAI API response.
    """
    try:
        content = response.choices[0].message.content.strip()
        # Attempt direct JSON parse:
        json_match = re.search(r"```json(.*?)```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content
        segments = json.loads(json_str)
        return segments
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        print("Raw content received:")
        print(content)
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None

def parse_gpt_segments(gpt_segments):
    """
    Ensure float fields, sorted by start.
    """
    final_segments = []
    for seg in gpt_segments:
        topic = seg.get("topic", "NoTopic").strip()
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        if end < start:
            continue
        final_segments.append({
            "topic": topic,
            "start": start,
            "end": end
        })
    final_segments.sort(key=lambda x: x["start"])
    return final_segments 
