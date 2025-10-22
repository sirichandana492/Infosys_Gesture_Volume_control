import cv2
import mediapipe as mp
import math

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

        # Flip for mirror effect
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convert BGR to RGB for MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks,
                                      mp_hands.HAND_CONNECTIONS)

            # Get coordinates of Thumb tip (id=4) and Index tip (id=8)
            thumb = hand_landmarks.landmark[4]
            index = hand_landmarks.landmark[8]

            x1, y1 = int(thumb.x * w), int(thumb.y * h)
            x2, y2 = int(index.x * w), int(index.y * h)

            # Draw circles on thumb & index tip
            cv2.circle(frame, (x1, y1), 8, (0, 0, 255), -1)
            cv2.circle(frame, (x2, y2), 8, (0, 255, 255), -1)

            # Draw line between them
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Calculate distance
            dist = math.hypot(x2 - x1, y2 - y1)
            cv2.putText(frame, f"Dist: {int(dist)}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Gesture Recognition - Distance Measurement", frame)

    # Exit on ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()