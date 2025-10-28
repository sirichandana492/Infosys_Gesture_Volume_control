import cv2
import mediapipe as mp
import pyautogui
import streamlit as st
import numpy as np
import time
import plotly.graph_objects as go
import pandas as pd

# ============ STREAMLIT CONFIG ============
st.set_page_config(page_title="Gesture Volume Control", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
h1, h2, h3 { color: #667eea !important; text-shadow: 0 0 10px rgba(102, 126, 234, 0.5); }
.metric-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(5px);
}
.metric-label { color: #b4a7d6; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
.metric-value { color: #f093fb; font-size: 2rem; font-weight: 800; text-shadow: 0 0 20px rgba(240, 147, 251, 0.5); }
.stButton>button { border-radius: 12px; padding: 12px 24px; font-weight: 700; border: none; transition: all 0.3s ease; }
.button-start { background: linear-gradient(90deg, #11998e, #38ef7d); color: white; }
.button-stop { background: linear-gradient(90deg, #fa709a, #fee140); color: white; }
.gesture-badge {
    display: inline-block;
    padding: 10px 20px;
    border-radius: 25px;
    font-weight: 700;
    margin: 5px;
    transition: all 0.3s ease;
}
.gesture-active { background: linear-gradient(90deg, #11998e, #38ef7d); color: white; box-shadow: 0 0 25px rgba(17, 153, 142, 0.6); }
.gesture-inactive { background: linear-gradient(90deg, #2c2c2c, #1a1a1a); color: #888; border: 1px solid #444; }
.status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.status-online { background: #38ef7d; box-shadow: 0 0 10px #38ef7d; }
.progress-bar-container { background: rgba(0, 0, 0, 0.3); border-radius: 10px; height: 40px; overflow: hidden; border: 2px solid rgba(102, 126, 234, 0.3); }
.progress-bar-fill { background: linear-gradient(90deg, #667eea, #764ba2, #f093fb); height: 100%; border-radius: 10px; transition: width 0.3s ease; box-shadow: 0 0 20px rgba(102, 126, 234, 0.5); }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
for key, default in {
    "logged_in": False, "username": "", "cap": None,
    "running": False, "paused": False, "last_volume_action": 0.0,
    "distance_history": [], "volume_history": [],
    "total_gestures": 0, "min_dist": 25, "max_dist": 160,
    "detection_conf": 0.6, "tracking_conf": 0.5,
    "current_dist": 0, "current_vol": 0, "current_fps": 0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============ UTILITY FUNCTIONS ============
def get_hand_state(hand_landmarks, img_shape):
    """Detect hand gesture: Open, Closed, or Pinched"""
    h, w, _ = img_shape
    thumb = hand_landmarks.landmark[4]
    index = hand_landmarks.landmark[8]
    middle = hand_landmarks.landmark[12]

    thumb_index_dist = np.hypot(index.x - thumb.x, index.y - thumb.y) * w
    thumb_middle_dist = np.hypot(middle.x - thumb.x, middle.y - thumb.y) * w

    if thumb_index_dist > 80 and thumb_middle_dist > 80:
        return "🖐 Open"
    elif thumb_index_dist < 40:
        return "🤏 Pinched"
    else:
        return "✊ Closed"


def open_camera():
    """Initialize camera capture"""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if cap.isOpened():
        st.session_state.cap = cap
        return True
    return False


def send_volume_action(dist, min_dist, max_dist):
    """Send volume control commands based on distance"""
    now = time.time()
    if dist < min_dist:
        action = "volumedown"
    elif dist > max_dist:
        action = "volumeup"
    else:
        return

    if (now - st.session_state.last_volume_action) > 0.12:
        try:
            pyautogui.press(action)
            st.session_state.total_gestures += 1
        except:
            pass
        st.session_state.last_volume_action = now


def draw_overlay(frame, dist, pct, fps, gesture):
    """Draw metrics overlay on video frame"""
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (260, 150), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    cv2.putText(frame, f"Distance: {dist}px", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (102, 126, 234), 2)
    cv2.putText(frame, f"Volume: {int(pct)}%", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 147, 251), 2)
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (56, 239, 125), 2)
    cv2.putText(frame, f"Gesture: {gesture}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 199, 0), 2)

    # Draw volume bar on right side
    bar_width, bar_height = 30, h - 80
    bar_x, bar_y = w - 45, 80
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
    fill_height = int((pct / 100) * bar_height)
    cv2.rectangle(frame, (bar_x, bar_y + bar_height - fill_height), (bar_x + bar_width, bar_y + bar_height),
                  (102, 126, 234), -1)
    cv2.putText(frame, f"{int(pct)}%", (bar_x + 35, bar_y + bar_height - fill_height + 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 2)

    return frame


def create_combined_chart():
    """Create analytics chart"""
    if not st.session_state.distance_history and not st.session_state.volume_history:
        return None

    fig = go.Figure()

    if st.session_state.distance_history:
        fig.add_trace(go.Scatter(
            x=list(range(len(st.session_state.distance_history))),
            y=st.session_state.distance_history,
            mode='lines',
            name='Distance',
            line=dict(color='#667eea', width=2),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))
        fig.add_hline(y=st.session_state.min_dist, line_dash="dash", line_color="#f093fb", annotation_text="Min")
        fig.add_hline(y=st.session_state.max_dist, line_dash="dash", line_color="#38ef7d", annotation_text="Max")

    fig.update_layout(
        title='Live Distance Monitor',
        xaxis_title='Time',
        yaxis_title='Distance (px)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )

    return fig


def do_login(username, password):
    """Authenticate user"""
    valid_users = {"siri": "password123", "admin": "admin123"}
    if username in valid_users and valid_users[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False


def do_logout():
    """Logout and cleanup"""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
    st.session_state.cap = None


# ============ LOGIN PAGE ============
if not st.session_state.logged_in:
    st.markdown("<div style='text-align: center; padding: 100px 0;'>", unsafe_allow_html=True)
    st.markdown("<h1>🔐 Gesture Control Login</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #b4a7d6; font-size: 1.1rem;'>Enter your credentials to access the system</p>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            if login_btn:
                if do_login(username.strip(), password):
                    st.success("✓ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ============ MAIN APP ============
st.markdown("<h1>Gesture Volume Control</h1>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color: #b4a7d6; font-size: 1.1rem;'>Welcome, <strong>{st.session_state.username}</strong> 👋</p>",
    unsafe_allow_html=True)

# Control buttons
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    if st.button("▶ Start", use_container_width=True, key="start"):
        if st.session_state.cap is None:
            open_camera()
        st.session_state.running = True
        st.session_state.paused = False
        st.rerun()

with col2:
    if st.session_state.running and not st.session_state.paused:
        if st.button("⏸ Pause", use_container_width=True, key="pause"):
            st.session_state.paused = True
            st.rerun()
    else:
        if st.button("▶ Resume", use_container_width=True, key="resume"):
            if st.session_state.running:
                st.session_state.paused = False
                st.rerun()

with col3:
    if st.button("⏹ Stop", use_container_width=True, key="stop"):
        st.session_state.running = False
        st.session_state.paused = False
        if st.session_state.cap:
            st.session_state.cap.release()
        st.session_state.cap = None
        st.session_state.distance_history = []
        st.session_state.volume_history = []
        st.rerun()

with col4:
    if st.button("🚪 Sign Out", use_container_width=True, key="logout"):
        do_logout()
        st.rerun()

# Status indicator
status_col1, status_col2, status_col3 = st.columns([1, 2, 1])
with status_col2:
    if st.session_state.running:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: linear-gradient(135deg, rgba(17, 153, 142, 0.2), rgba(56, 239, 125, 0.2)); 
                    border: 2px solid #38ef7d; border-radius: 12px; margin: 10px 0;'>
            <span class='status-indicator status-online'></span>
            <strong style='color: #38ef7d; font-size: 1.2rem;'>System Active</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align: center; padding: 15px; background: rgba(136, 136, 136, 0.1); 
                    border: 2px solid #888; border-radius: 12px; margin: 10px 0;'>
            <span class='status-indicator'></span>
            <strong style='color: #888; font-size: 1.2rem;'>System Offline</strong>
        </div>
        """, unsafe_allow_html=True)

# Main layout
col_left, col_right = st.columns([1.5, 1])

with col_left:
    video_placeholder = st.empty()

with col_right:
    st.markdown("<h3 style='color: #f093fb; text-align: center;'>📊 Live Metrics</h3>", unsafe_allow_html=True)

    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        distance_metric = st.empty()
    with metric_col2:
        volume_metric = st.empty()

    metric_col3, metric_col4 = st.columns(2)
    with metric_col3:
        fps_metric = st.empty()
    with metric_col4:
        gestures_metric = st.empty()

    st.markdown("<h3 style='color: #f093fb; text-align: center; margin-top: 15px;'>🎯 Gesture Status</h3>",
                unsafe_allow_html=True)
    gesture_box = st.empty()

    st.markdown("<h3 style='color: #f093fb; text-align: center; margin-top: 15px;'>🔊 Volume Level</h3>",
                unsafe_allow_html=True)
    volume_vis = st.empty()

    st.markdown("<h3 style='color: #f093fb; text-align: center; margin-top: 20px;'>📈 Analytics</h3>",
                unsafe_allow_html=True)
    chart_placeholder = st.empty()

# Settings
st.markdown("---")
with st.expander("⚙ Advanced Settings", expanded=False):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("📏 Distance Calibration**")
        min_dist = st.number_input("Min Distance (px)", 10, 100, int(st.session_state.min_dist))
        max_dist = st.number_input("Max Distance (px)", 100, 300, int(st.session_state.max_dist))
        if st.button("Apply Calibration"):
            st.session_state.min_dist = min_dist
            st.session_state.max_dist = max_dist
            st.success("✓ Calibration updated!")

    with col_s2:
        st.markdown("🎯 Detection Settings**")
        det_conf = st.slider("Detection Confidence", 0.5, 0.9, float(st.session_state.detection_conf), 0.05)
        track_conf = st.slider("Tracking Confidence", 0.4, 0.8, float(st.session_state.tracking_conf), 0.05)
        if st.button("Apply Settings"):
            st.session_state.detection_conf = det_conf
            st.session_state.tracking_conf = track_conf
            st.success("✓ Settings updated!")

# ============ CAMERA LOOP ============
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

if st.session_state.running and st.session_state.cap and not st.session_state.paused:
    cap = st.session_state.cap
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=st.session_state.detection_conf,
                        min_tracking_confidence=st.session_state.tracking_conf) as hands:
        prev_time, fps = time.time(), 0.0

        while st.session_state.running and not st.session_state.paused:
            ok, frame = cap.read()
            if not ok:
                video_placeholder.markdown("<div class='metric-card'>⚠ Waiting for camera feed...</div>",
                                           unsafe_allow_html=True)
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            dist, pct, hand_state = 0, 0, "—"

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                           mp_draw.DrawingSpec(color=(102, 126, 234), thickness=2, circle_radius=1),
                                           mp_draw.DrawingSpec(color=(240, 147, 251), thickness=2))

                    thumb = hand_landmarks.landmark[4]
                    index = hand_landmarks.landmark[8]
                    h, w, _ = frame.shape
                    tx, ty = int(thumb.x * w), int(thumb.y * h)
                    ix, iy = int(index.x * w), int(index.y * h)

                    cv2.line(frame, (tx, ty), (ix, iy), (102, 126, 234), 3)
                    cv2.circle(frame, (tx, ty), 8, (240, 147, 251), -1)
                    cv2.circle(frame, (ix, iy), 8, (56, 239, 125), -1)

                    dist = int(np.hypot(ix - tx, iy - ty))
                    pct = np.clip((dist - st.session_state.min_dist) / (
                                st.session_state.max_dist - st.session_state.min_dist) * 100, 0, 100)

                    send_volume_action(dist, st.session_state.min_dist, st.session_state.max_dist)
                    hand_state = get_hand_state(hand_landmarks, frame.shape)

                    cv2.putText(frame, f"{dist}px", (min(tx, ix) + 10, min(ty, iy) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (255, 255, 255), 2)

            st.session_state.distance_history.append(dist)
            st.session_state.volume_history.append(pct)
            if len(st.session_state.distance_history) > 100:
                st.session_state.distance_history.pop(0)
                st.session_state.volume_history.pop(0)

            frame = draw_overlay(frame, dist, pct, fps, hand_state)

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1 / (now - prev_time)) if (now - prev_time) > 0 else fps
            prev_time = now

            st.session_state.current_dist = dist
            st.session_state.current_vol = pct
            st.session_state.current_fps = fps

            video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)

            distance_metric.markdown(
                f"<div class='metric-card'><div class='metric-label'>Distance</div><div class='metric-value'>{dist}</div></div>",
                unsafe_allow_html=True)
            volume_metric.markdown(
                f"<div class='metric-card'><div class='metric-label'>Volume</div><div class='metric-value'>{int(pct)}%</div></div>",
                unsafe_allow_html=True)
            fps_metric.markdown(
                f"<div class='metric-card'><div class='metric-label'>FPS</div><div class='metric-value'>{int(fps)}</div></div>",
                unsafe_allow_html=True)
            gestures_metric.markdown(
                f"<div class='metric-card'><div class='metric-label'>Gestures</div><div class='metric-value'>{st.session_state.total_gestures}</div></div>",
                unsafe_allow_html=True)

            gesture_box.markdown(f"""
            <div style='text-align: center; padding: 15px;'>
                <div class="gesture-badge {'gesture-active' if hand_state == '🖐 Open' else 'gesture-inactive'}">🖐 Open</div>
                <div class="gesture-badge {'gesture-active' if hand_state == '✊ Closed' else 'gesture-inactive'}">✊ Closed</div>
                <div class="gesture-badge {'gesture-active' if hand_state == '🤏 Pinched' else 'gesture-inactive'}">🤏 Pinched</div>
            </div>
            """, unsafe_allow_html=True)

            volume_vis.markdown(f"""
            <div style='padding: 10px;'>
                <div class='progress-bar-container'>
                    <div class='progress-bar-fill' style='width: {pct}%;'></div>
                </div>
                <div style='text-align: center; margin-top: 10px; font-size: 1.5rem; font-weight: 800; color: #f093fb;'>{int(pct)}%</div>
            </div>
            """, unsafe_allow_html=True)

            chart = create_combined_chart()
            if chart:
                chart_placeholder.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})

elif st.session_state.paused:
    video_placeholder.markdown(
        "<div class='metric-card'><h2 style='color: #f5576c; text-align: center;'>⏸ System Paused</h2></div>",
        unsafe_allow_html=True)
    chart = create_combined_chart()
    if chart:
        chart_placeholder.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})

elif not st.session_state.running:
    video_placeholder.markdown("""
    <div style='text-align: center; padding: 60px 20px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); 
                border: 2px solid rgba(102, 126, 234, 0.3); border-radius: 15px;'>
        <h1 style='color: #667eea; margin-bottom: 20px;'>🎥 Ready to Start</h1>
        <p style='color: #b4a7d6; font-size: 1.2rem;'>Click the <strong style='color: #38ef7d;'>Start</strong> button to begin</p>
    </div>
    """, unsafe_allow_html=True)
    chart = create_combined_chart()
    if chart:
        chart_placeholder.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})