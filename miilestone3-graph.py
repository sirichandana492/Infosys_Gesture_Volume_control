import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, Response, render_template_string, jsonify
import threading
import time
import webbrowser
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ----------------- SETUP -----------------
app = Flask(__name__)

# Mediapipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# System volume (Pycaw) - FIX: use _iid_ attribute
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume_ctrl.GetVolumeRange()
min_vol, max_vol = vol_range[0], vol_range[1]

# Globals
MAX_DIST = 150
MIN_DIST = 10
current_volume = 0
camera_running = True

# ----------------- FRAME GENERATOR -----------------
def generate_frames():
    global current_volume, camera_running, cap
    while camera_running:
        success, frame = cap.read()
        if not success:
            # small sleep to avoid busy loop if camera fails
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        # Read current system volume from Windows (0–100)
        try:
            sys_vol_db = volume_ctrl.GetMasterVolumeLevel()
            sys_vol_percent = int(np.interp(sys_vol_db, [min_vol, max_vol], [0, 100]))
        except Exception:
            sys_vol_percent = 0

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                h, w, _ = frame.shape
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
                index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)

                cv2.circle(frame, (thumb_x, thumb_y), 8, (255, 0, 0), -1)
                cv2.circle(frame, (index_x, index_y), 8, (0, 255, 0), -1)
                cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 0, 255), 3)

                # Calculate distance
                distance = int(((index_x - thumb_x) ** 2 + (index_y - thumb_y) ** 2) ** 0.5)
                cv2.putText(frame, f"Dist: {distance}px", (thumb_x, thumb_y - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                # Map distance to volume
                distance_clamped = np.clip(distance, MIN_DIST, MAX_DIST)
                vol_percent = np.interp(distance_clamped, [MIN_DIST, MAX_DIST], [0, 100])
                vol_db = float(np.interp(vol_percent, [0, 100], [min_vol, max_vol]))

                # Only update if large change (for smoothness)
                if abs(vol_percent - sys_vol_percent) > 2:
                    try:
                        volume_ctrl.SetMasterVolumeLevel(vol_db, None)
                    except Exception as e:
                        # ignore volume set failures (permission / device issues)
                        print("Volume set error:", e)

                # read back current volume
                try:
                    current_volume = int(np.interp(volume_ctrl.GetMasterVolumeLevel(),
                                                   [min_vol, max_vol], [0, 100]))
                except Exception:
                    current_volume = int(vol_percent)

                # Draw volume bar
                bar_x, bar_y = 40, 100
                bar_width, bar_height = 25, 300
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
                fill_height = int((current_volume / 100) * bar_height)
                cv2.rectangle(frame, (bar_x, bar_y + bar_height - fill_height),
                              (bar_x + bar_width, bar_y + bar_height), (0, 255, 0), -1)
                cv2.putText(frame, f"{current_volume}%", (bar_x - 5, bar_y + bar_height + 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    # cleanup
    try:
        cap.release()
    except Exception:
        pass

# ----------------- ROUTES -----------------
@app.route("/video_feed")
def video_feed():
    global camera_running
    camera_running = True
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/stop_camera")
def stop_camera():
    global camera_running
    camera_running = False
    return jsonify(status="Camera stopped")

@app.route("/volume_data")
def volume_data():
    try:
        sys_vol_db = volume_ctrl.GetMasterVolumeLevel()
        sys_vol_percent = int(np.interp(sys_vol_db, [min_vol, max_vol], [0, 100]))
    except Exception:
        sys_vol_percent = current_volume
    return jsonify(volume=sys_vol_percent, timestamp=time.time())

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎛 Gesture Volume Control — Windows Synced</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { background: #0d0d0d; color: white; font-family: Arial; text-align: center; }
            h2 { color: #00ffcc; }
            .container { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 40px; }
            img { border: 3px solid #00ffcc; border-radius: 10px; width: 640px; height: 480px; }
            canvas { background: #1a1a1a; border-radius: 10px; padding: 10px; width: 400px; height: 300px; }
            button {
                background: #ff4d4d; color: white; border: none; border-radius: 6px;
                padding: 10px 20px; font-size: 16px; margin-top: 15px; cursor: pointer; transition: 0.2s;
            }
            button:hover { background: #ff6666; }
        </style>
    </head>
    <body>
        <h2>✋ Hand Gesture Volume Control (Windows Synced)</h2>
        <div class="container">
            <div>
                <img id="videoFeed" src="/video_feed">
                <br><button onclick="stopCamera()">🛑 Stop Camera</button>
            </div>
            <div>
                <canvas id="volumeChart"></canvas>
            </div>
        </div>

        <script>
        const ctx = document.getElementById('volumeChart').getContext('2d');
        const data = { labels: [], datasets: [{ label: 'System Volume %', data: [], borderColor: '#00ffcc', fill: true, backgroundColor: 'rgba(0,255,204,0.2)', tension: 0.4 } ]};
        const chart = new Chart(ctx, { type: 'line', data: data, options: { animation: { duration: 0 }, scales: { y: { min: 0, max: 100, ticks: { color: '#ccc' }}, x: { ticks: { color: '#ccc' }}}}});

        async function updateChart() {
            try {
                const res = await fetch('/volume_data');
                const v = await res.json();
                const label = new Date(v.timestamp * 1000).toLocaleTimeString();
                data.labels.push(label);
                data.datasets[0].data.push(v.volume);
                if (data.labels.length > 30) { data.labels.shift(); data.datasets[0].data.shift(); }
                chart.update();
            } catch (e) {
                // ignore fetch errors
            }
        }

        async function stopCamera() {
            await fetch('/stop_camera');
            document.getElementById('videoFeed').src = '';
            alert("Camera stopped!");
        }

        setInterval(updateChart, 200);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# ----------------- AUTO OPEN -----------------
def open_browser():
    time.sleep(1)
    try:
        webbrowser.open("http://127.0.0.1:5000")
    except Exception:
        pass

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    # run Flask
    app.run(host="0.0.0.0", port=5000, threaded=True)
