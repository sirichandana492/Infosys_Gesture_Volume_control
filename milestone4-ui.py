import cv2
import mediapipe as mp
import pyautogui
import streamlit as st
import numpy as np
import time

# ---------------- Streamlit Config ----------------
st.set_page_config(page_title="Gesture Volume Control", layout="wide")

st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #050505, #0a192f);
    color: #e6f7f2;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3 {
    color: #00e0b8;
    text-shadow: 0 0 10px #00e0b8;
}
.stTextInput>div>div>input, .stPassword>div>div>input {
    background-color: #0a192f;
    color: #e6f7f2 !important;
    border: 1px solid #00e0b8;
    border-radius: 8px;
}
.stButton>button {
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    background: linear-gradient(90deg, #00e0b8, #0099ff);
    color: black;
    border: none;
    box-shadow: 0 0 8px #00e0b8;
    transition: 0.3s;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #00ffa2, #00b7ff);
    box-shadow: 0 0 15px #00ffa2;
}
.status-box {
    background-color: rgba(0,255,224,0.08);
    border: 1px solid rgba(0,255,224,0.3);
    padding: 15px;
    border-radius: 8px;
    font-size: 1.3em;
    line-height: 1.8em;
}
.metric-label {
    color: #00ffcc;
    font-weight: 700;
}
.metric-value {
    color: #ff66cc;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Credentials ----------------
VALID_USERS = {"siri": "password123", "admin": "admin123"}

# ---------------- Session State ----------------
for key, default in {
    "logged_in": False, "username": "", "cap": None,
    "running": False, "last_volume_action": 0.0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- Utility Functions ----------------
def get_hand_state(hand_landmarks, img_shape):
    h, w, _ = img_shape
    tips_ids = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    pip_ids = [6, 10, 14, 18]   # Their lower joints
    open_count = 0

    # Count fingers that are open
    for tip, pip in zip(tips_ids, pip_ids):
        if hand_landmarks.landmark[tip].y * h < hand_landmarks.landmark[pip].y * h:
            open_count += 1

    # Check thumb position
    thumb_tip_x = hand_landmarks.landmark[4].x * w
    thumb_ip_x = hand_landmarks.landmark[3].x * w
    if thumb_tip_x > thumb_ip_x:
        open_count += 1

    if open_count >= 5:
        return "🖐️ Open"
    elif open_count <= 1:
        return "✊ Closed"
    else:
        return "🤏 Pinched"

def draw_volume_bar_on_frame(frame, pct):
    h, w, _ = frame.shape
    bar_h = int((pct / 100.0) * (h - 40))
    x1, x2 = w - 40, w - 20
    y2, y1 = h - 20, h - 20 - bar_h
    cv2.rectangle(frame, (x1, 20), (x2, y2), (50, 50, 50), 2)
    cv2.rectangle(frame, (x1 + 2, y1 + 2), (x2 - 2, y2 - 2), (0, 255, 128), -1)
    cv2.putText(frame, f"{int(pct)}%", (x1 - 60, y1 + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return frame

def open_camera():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if cap.isOpened():
        st.session_state.cap = cap
        return True
    return False

def maybe_send_volume_action(dist, min_dist, max_dist):
    now = time.time()
    if dist < min_dist:
        action = "volumedown"
    elif dist > max_dist:
        action = "volumeup"
    else:
        action = None

    if action and (now - st.session_state.last_volume_action) > 0.12:
        try:
            pyautogui.press(action)
        except:
            pass
        st.session_state.last_volume_action = now

def do_login(username, password):
    if username in VALID_USERS and VALID_USERS[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.running = False
    else:
        st.error("❌ Invalid username or password!")

def do_logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
    st.session_state.cap = None

# ---------------- Login Page ----------------
if not st.session_state.logged_in:
    st.title("🔐 Login — Gesture Volume Control")
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        if login_btn:
            do_login(username.strip(), password)
    st.stop()

# ---------------- Main App ----------------
st.title("🎛 Gesture Volume Control")
st.caption(f"Signed in as: **{st.session_state.username}**")

col1, col2, col3 = st.columns([1, 1, 1])
if col3.button("🚪 Sign Out"):
    do_logout()
    st.rerun()

start_btn = col1.button("🎥 Start Camera")
stop_btn = col2.button("🛑 Stop Camera")

video_col, info_col = st.columns([2, 1])
video_placeholder = video_col.empty()
info_box = info_col.empty()

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
MIN_DIST, MAX_DIST = 25, 160

# Start Camera
if start_btn:
    if st.session_state.cap is None:
        open_camera()
    st.session_state.running = True

# Stop Camera
if stop_btn:
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
    st.session_state.cap = None
    video_placeholder.image("https://via.placeholder.com/640x480.png?text=Camera+Stopped", use_container_width=True)
    info_box.markdown("<div class='status-box'>Camera stopped. Click <b>🎥 Start Camera</b> to resume.</div>", unsafe_allow_html=True)

# ---------------- Camera Loop ----------------
if st.session_state.running and st.session_state.cap:
    cap = st.session_state.cap
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5) as hands:
        prev_time, fps = time.time(), 0.0
        while st.session_state.running:
            ok, frame = cap.read()
            if not ok:
                info_box.markdown("<div class='status-box'>⚠️ Waiting for camera feed...</div>", unsafe_allow_html=True)
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            dist, pct = 0, 0
            status = "🎚 Stable"
            hand_state = "—"

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    h, w, _ = frame.shape
                    tx, ty, ix, iy = int(thumb.x * w), int(thumb.y * h), int(index.x * w), int(index.y * h)
                    cv2.line(frame, (tx, ty), (ix, iy), (0, 255, 255), 2)
                    dist = int(np.hypot(ix - tx, iy - ty))
                    pct = np.clip((dist - MIN_DIST) / (MAX_DIST - MIN_DIST) * 100, 0, 100)
                    maybe_send_volume_action(dist, MIN_DIST, MAX_DIST)

                    if dist < MIN_DIST:
                        status = "🔉 Decreasing"
                    elif dist > MAX_DIST:
                        status = "🔊 Increasing"

                    hand_state = get_hand_state(hand_landmarks, frame.shape)

                    cv2.putText(frame, f"{dist}px", (min(tx, ix) + 6, min(ty, iy) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            frame = draw_volume_bar_on_frame(frame, pct)
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1 / (now - prev_time)) if (now - prev_time) > 0 else fps
            prev_time = now

            video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
            info_box.markdown(f"""
            <div class='status-box'>
            <span class='metric-label'>Distance:</span> <span class='metric-value'>{dist}px</span><br>
            <span class='metric-label'>Volume:</span> <span class='metric-value'>{int(pct)}%</span><br>
            <span class='metric-label'>Status:</span> <span class='metric-value'>{status}</span><br>
            <span class='metric-label'>Hand Gesture:</span> <span class='metric-value'>{hand_state}</span><br>
            <span class='metric-label'>FPS:</span> <span class='metric-value'>{int(fps)}</span>
            </div>
            """, unsafe_allow_html=True)
