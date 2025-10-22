🧠 PROJECT OVERVIEW

This project demonstrates contactless volume control using computer vision and hand-tracking technology. The system recognizes hand gestures in real-time and adjusts the system volume based on the distance between the thumb and index finger. It uses MediaPipe for hand landmark detection and OpenCV for visualizing gestures on the webcam feed.

🔍 OBJECTIVE

To develop an AI-based gesture recognition system that allows users to control volume without physical contact — making it an interactive, hygienic, and modern way to interact with digital devices.

⚙️ TECHNOLOGIES USED

🐍 Python

📸 OpenCV — for real-time camera access and image processing ✋ MediaPipe — for detecting and tracking hand landmarks 🔊 PyCaw / PyAutoGUI / OS module — for controlling system or media volume


✨ Features

✅ Real-time hand detection using MediaPipe Hands
✅ Smooth and responsive volume adjustment
✅ Visual feedback (e.g., volume bar / circular gauge)
✅ Works on any system with a webcam
✅ Simple Streamlit-based GUI
✅ Optional Login page for secure access
✅ FPS (Frames per Second) display for performance monitoring

🧩 PROJECT MODULES

1️⃣ Gesture Recognition Detects the hand using MediaPipe. Identifies landmarks such as fingertips and joints.

2️⃣ Distance Measurement Module Calculates the Euclidean distance between thumb and index fingertips. Maps that distance to the volume range (0% – 100%).

3️⃣ System Volume Control Converts hand distance to system volume level. Displays a green progress bar indicating the current volume percentage.

📈 WORKING PRINCIPLE The webcam captures the real-time video feed. MediaPipe detects the hand and locates landmarks. The distance between the thumb and index finger tips is calculated.

Based on this distance: Short distance → Low volume Large distance → High volume

The bar on the screen visually represents the volume level in percentage.

💡 FEATURES

✅ Real-time hand detection ✅ Contactless volume control ✅ Dynamic visual feedback ✅ Cross-platform (works on Windows, Linux, Mac) ✅ Easy to integrate and modify

🧠 FUTURE ENHANCEMENTS

Add gesture-based mute/unmute functionality. Integrate with YouTube / Spotify volume control. Implement multi-hand control for dual actions. Enhance accuracy using AI-based gesture classification.
