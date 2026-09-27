import cv2
import serial
import time

# Ouvre la connexion série vers l'ESP32
esp = serial.Serial('COM3', 115200)  # Remplace COM3 par le bon port

# Charge le classificateur de visages
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Ouvre la webcam
cap = cv2.VideoCapture(0)

# Tu peux améliorer ça avec un système d'identification (facenet, deepface...)
def detect_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    return faces

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = detect_face(frame)
    for (x, y, w, h) in faces:
        # Dessine un rectangle autour du visage
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Envoie le signal à l'ESP32
        print("Visage détecté ! Envoi à ESP32...")
        esp.write(b"UNLOCK\n")
        time.sleep(5)  # Attente pour éviter répétition

    cv2.imshow('Camera', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
