🎛️ Gesture Volume Control using Hand Gestures

Control your system volume effortlessly with just your hand gestures — no need to touch your keyboard or mouse!
This project uses computer vision and hand-tracking technology powered by OpenCV, MediaPipe, and PyAutoGUI to adjust your device’s volume based on the distance between your fingers in real time.

🧠 Project Overview

This project allows users to increase or decrease system volume using predefined hand gestures detected through the webcam.
By tracking specific landmarks of your hand (like the thumb and index finger tips), it measures their distance and maps it to the system volume level dynamically.

It’s built with Python and runs on a simple, clean Streamlit web interface for ease of use.
✨ Features

✅ Real-time hand detection using MediaPipe Hands
✅ Smooth and responsive volume adjustment
✅ Visual feedback (e.g., volume bar / circular gauge)
✅ Works on any system with a webcam
✅ Simple Streamlit-based GUI
✅ Optional Login page for secure access
✅ FPS (Frames per Second) display for performance monitoring

🧩 Tech Stack
Component	Technology Used
Programming Language	Python 🐍
Computer Vision	OpenCV
Hand Tracking	MediaPipe
System Control	PyAutoGUI / PyCaw
Web Interface	Streamlit
Visualization	Matplotlib / Numpy
⚙️ How It Works

The webcam captures live video frames.

MediaPipe Hands detects and tracks hand landmarks in real time.

The distance between the thumb and index finger tips is calculated.

This distance is mapped to the system’s volume level using PyAutoGUI or PyCaw.

The adjusted volume level is shown visually on the interface.

Optionally, the app includes a login page for secure usage.
Requirements

Install the required Python libraries using pip:

pip install opencv-python mediapipe pyautogui streamlit numpy matplotlib
🔧 Future Enhancements

Add gesture-based mute/unmute

Multi-hand support for more controls (brightness, playback, etc.)

Integration with voice assistant or IoT devices

Customizable gesture mappings
