import cv2
import mediapipe as mp

# ---- Webcam input ----
webcam = cv2.VideoCapture(0)  # open default webcam

# ---- Hand detection model ----
my_hands = mp.solutions.hands.Hands()
drawing_utils = mp.solutions.drawing_utils

while True:
    ret, image = webcam.read()
    if not ret:
        break

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # run the hand-detection model
    output = my_hands.process(rgb_image)
    hands = output.multi_hand_landmarks

    # draw landmarks if any hands are detected
    if hands:
        for hand in hands:
            drawing_utils.draw_landmarks(image, hand)

    cv2.imshow("Webcam + Hand Detection", image)

    if cv2.waitKey(10) & 0xFF == 27:
        break
webcam.release()
cv2.destroyAllWindows()