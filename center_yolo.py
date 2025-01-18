import cv2
import subprocess
from ultralytics import YOLO

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


def create_reel(frame, person_bbox, output_path):
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
    resized = cv2.resize(cropped, (target_width, target_height))
    
    # Save the frame
    i = output_path.replace("output_reel_", "").replace(".mp4", "")
    cv2.imwrite(f"temp_frame_{i}.jpg", resized)
    
    # Use FFmpeg to create a video from the frame
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", f"temp_frame_{i}.jpg",
        "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p",
        output_path
    ])


def join_images_to_video(output_path):
    subprocess.run([
        "ffmpeg", "-framerate", "30", "-i", "temp_frame_%d.jpg",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        output_path
    ])

# Load YOLOv8 model
model = YOLO('yolov8n.pt')  # Load the smallest YOLOv8 model


# Process video
input_video = "original_video.mp4"
output_video = "output_reel.mp4"

i = 0
for frame in get_all_frames(input_video):
    if frame is not None:
        person_bbox = detect_person(frame, model)
        if person_bbox:
            create_reel(frame, person_bbox, f"{output_video.replace('.mp4', '')}_{i}.mp4")
            print("Reel created successfully!")
        else:
            print("No person detected in the first frame.")
        print(i)
        i += 1
    else:
        print("Failed to read the input video.")


join_images_to_video("output_reel.mp4")