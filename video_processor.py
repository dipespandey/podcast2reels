import os
import subprocess
from center_yolo import process_video_with_stabilization

def generate_ass_subtitles_for_chunk(subtitle_lines, chunk_start, chunk_end, output_ass_path):
    """
    Generate an .ass file with a custom style "TikTokFunky":
      - Big, bold, centered in the middle of the screen
      - We'll use \fad(500,500) on each line for a simple fade in/out
    """
    def to_ass_time(sec):
        # Convert absolute time to chunk-relative
        rel = sec - chunk_start
        if rel < 0:
            rel = 0
        hours = int(rel // 3600)
        minutes = int((rel % 3600) // 60)
        seconds = int(rel % 60)
        centisec = int(round((rel - int(rel)) * 100))
        return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{centisec:02d}"

    # .ass header + style definition
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
Title: TikTok-Style Subtitles
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: TikTokFunky,Comic Sans MS,60,&H00FFB7FF,&H00000000,&H00000000,1,0,0,0,100,100,0,1,3,1,5,10,10,30,0

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    dialogue_lines = []
    for item in subtitle_lines:
        abs_start = item["start"]
        abs_end = abs_start + item["duration"]
        if abs_end > chunk_end:
            abs_end = chunk_end

        # Skip if entirely outside
        if abs_start >= chunk_end or abs_end <= chunk_start:
            continue

        start_ts = to_ass_time(abs_start)
        end_ts = to_ass_time(abs_end)
        # Add a fade in/out with \fad(500,500) for 0.5s fade in/out
        text = item["text"].replace("\n", " ").replace(",", "，")
        text = "{\\fad(500,500)}" + text

        # Dialogue line
        dialogue = f"Dialogue: 0,{start_ts},{end_ts},TikTokFunky,,0,0,0,,{text}"
        dialogue_lines.append(dialogue)

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(dialogue_lines))

def cut_video_with_subtitles(
    video_path,
    segments,
    transcript_data,
    output_folder="topic_segments",
    vertical=False,
):
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i, seg in enumerate(segments, start=1):
        seg_start = seg["start"]
        seg_end = seg["end"]
        duration = seg_end - seg_start
        if duration <= 0:
            continue

        topic_label = seg["topic"] or f"segment_{i}"
        safe_topic = "".join(c for c in topic_label if c.isalnum() or c in " _-").strip()
        safe_topic = safe_topic[:50]  # Limit length
        
        # Define output file paths
        out_chunk = os.path.abspath(os.path.join(
            output_folder, f"{seg_start:.2f}_{safe_topic}.mp4"))
        out_ass = os.path.abspath(os.path.join(
            output_folder, f"{seg_start:.2f}_{safe_topic}.ass"))
        
        if vertical:
            out_chunk_centered = os.path.abspath(os.path.join(
                output_folder, f"{seg_start:.2f}_{safe_topic}_centered.mp4"))
            out_ass_centered = os.path.abspath(os.path.join(
                output_folder, f"{seg_start:.2f}_{safe_topic}_centered.ass"))

        try:
            # Create subtitles for the segment
            generate_ass_subtitles_for_chunk(
                subtitle_lines=transcript_data,
                chunk_start=seg_start,
                chunk_end=seg_end,
                output_ass_path=out_ass,
            )

            # create without cropping and subtitles 
            cmd = [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-ss", str(seg_start),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                out_chunk
            ]

            print(f"[INFO] Running ffmpeg command for segment {i}:")
            print(f"[INFO] Command: {' '.join(cmd)}")
            
            # Execute FFmpeg to cut the video chunk
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Check if the output file was created successfully
            if not os.path.exists(out_chunk) or os.path.getsize(out_chunk) == 0:
                print(f"[ERROR] Failed to create video segment {i}. FFmpeg output:")
                print(result.stderr)
                continue

            print(f"[INFO] Successfully created segment {i}: {out_chunk}")
            print(f"      Topic: {topic_label}, Start={seg_start}, End={seg_end}")

            # Properly escape the subtitle path for ffmpeg
            escaped_ass = out_ass.replace("'", "'\\''")
            # Build filter string for vertical/horizontal video
           
            filter_sub = (
                f"scale=-1:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
                f"subtitles='{escaped_ass}':force_style='FontName=Arial,FontSize=24'"
            )

            if vertical:
                process_video_with_stabilization(out_chunk, out_chunk_centered, filter_sub, 150)

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] FFmpeg command failed for segment {i}: {e}")
            print(f"FFmpeg stderr output: {e.stderr}")
            continue
        except Exception as e:
            print(f"[ERROR] Failed to process segment {i}: {str(e)}")
            continue 