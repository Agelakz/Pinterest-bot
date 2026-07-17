import cv2
import os

video_path = "/home/ubuntu/pinterest-bot/temp/media_8868e6fe.mp4" # From previous logs, if exists
if not os.path.exists(video_path):
    print("Video not found, using any mp4 in temp")
    import glob
    videos = glob.glob("/home/ubuntu/pinterest-bot/temp/*.mp4")
    if videos:
        video_path = videos[0]
    else:
        print("No videos found to test.")
        exit(1)

print(f"Testing extraction from {video_path}")
cap = cv2.VideoCapture(video_path)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cover_path = "/home/ubuntu/pinterest-bot/temp/test_cover.jpg"
        cv2.imwrite(cover_path, frame)
        print(f"Success! Saved to {cover_path}")
        print(f"Size: {os.path.getsize(cover_path)}")
    else:
        print("Failed to read frame")
    cap.release()
else:
    print("Failed to open video")
