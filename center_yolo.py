import cv2
import subprocess
import numpy as np
from ultralytics import YOLO
import os

def get_first_frame(input_video):
    cap = cv2.VideoCapture(input_video)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def get_all_frames(input_video):
    cap = cv2.VideoCapture(input_video)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def detect_person(frame, model):
    results = model(frame)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls == 0:  # 0 is typically the class ID for person in COCO dataset
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                return (int((x1 + x2) / 2), int((y1 + y2) / 2), int(x2 - x1), int(y2 - y1))
    return None

def euclidean_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def create_reel_frame(frame, person_bbox):
    """Create a single frame for the reel with the given bbox"""
    center_x, center_y, w, h = person_bbox
    frame_height, frame_width = frame.shape[:2]
    
    target_width = 1080
    target_height = 1920
    
    # Calculate the crop region
    crop_width = min(frame_width, int(target_width * frame_height / target_height))
    crop_height = frame_height
    
    left = max(0, center_x - crop_width // 2)
    right = min(frame_width, left + crop_width)
    
    # Adjust if the crop goes out of bounds
    if left == 0:
        right = crop_width
    elif right == frame_width:
        left = frame_width - crop_width
    
    cropped = frame[:, left:right]
    
    # Resize to target dimensions
    return cv2.resize(cropped, (target_width, target_height))

def process_video_with_stabilization(input_video, output_video, model, movement_threshold=500):
    """Process video with stabilization to reduce jitter"""
    
    frames = get_all_frames(input_video)
    if not frames:
        print("No frames found in the video")
        return
    
    # Get video properties
    frame_height, frame_width = frames[0].shape[:2]
    fps = 30
    
    # Create temporary video for processed frames
    temp_video = output_video.replace('.mp4', '_temp.mp4')
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (1080, 1920))
    
    # Initialize variables for stabilization
    last_stable_bbox = None
    processed_frames = []
    
    print(f"Processing {len(frames)} frames...")
    
    # First pass: Detect person in each frame and apply stabilization
    for i, frame in enumerate(frames):
        current_bbox = detect_person(frame, model)
        
        if current_bbox is None:
            # If no person detected, use last stable bbox if available
            if last_stable_bbox is not None:
                current_bbox = last_stable_bbox
            else:
                # If no previous bbox, use center of frame
                center_x = frame_width // 2
                center_y = frame_height // 2
                current_bbox = (center_x, center_y, frame_width // 3, frame_height // 2)
        
        if last_stable_bbox is None:
            # First detection becomes the stable bbox
            last_stable_bbox = current_bbox
        else:
            # Check if movement exceeds threshold
            current_center = (current_bbox[0], current_bbox[1])
            last_center = (last_stable_bbox[0], last_stable_bbox[1])
            
            if euclidean_distance(current_center, last_center) < movement_threshold:
                # Movement is small, use the last stable bbox
                current_bbox = last_stable_bbox
            else:
                # Movement is significant, update the stable bbox
                last_stable_bbox = current_bbox
        
        # Create the frame with current bbox
        processed_frame = create_reel_frame(frame, current_bbox)
        processed_frames.append(processed_frame)
        
        if i % 10 == 0:
            print(f"Processed frame {i}/{len(frames)}")
    
    # Write processed frames to video
    for frame in processed_frames:
        out.write(frame)
    
    out.release()
    print("Video processing complete!")
    
    # Convert to web-compatible format and add audio using ffmpeg
    web_output = output_video.replace('.mp4', '_web.mp4')
    
    try:
        subprocess.run([
            'ffmpeg', '-y',
            '-i', temp_video,  # Processed video
            '-i', input_video,  # Original video (for audio)
            '-c:v', 'libx264',  # Video codec
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',  # Audio codec
            '-map', '0:v:0',  # Use video from first input
            '-map', '1:a:0?',  # Use audio from second input if it exists
            '-shortest',  # End when shortest input ends
            '-movflags', '+faststart',
            web_output
        ], check=True)
        
        # Clean up temporary files
        os.remove(temp_video)
        
        # Replace original output with web-compatible version
        os.replace(web_output, output_video)
        
        print("Final video with audio created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")
        if os.path.exists(temp_video):
            os.remove(temp_video)
        if os.path.exists(web_output):
            os.remove(web_output)
        raise


def main():

    # Load YOLOv8 model
    model = YOLO('yolov8n.pt')  # Load the smallest YOLOv8 model

    # Process video
    input_video = "original_video.mp4"
    output_video = "output_reel.mp4"
    process_video_with_stabilization(input_video, output_video, model)


if __name__ == "__main__":
    main()
