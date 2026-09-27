import serial
import time
import face_recognition
import cv2
import os
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# --- Paramètres ---
face_timeout = 5  # secondes pendant lesquelles on attend un visage avant de passer au QR
qr_valides = ["khaled"]  # QR codes autorisés
database_path = "C:\\Users\\Khaled\\Desktop\\CameraFaceRecognitionDoorLock\\known faces"

# --- Chargement des visages ---
known_faces = []
labels = []
classes = os.listdir(database_path)

for i, person in enumerate(classes):
    person_path = os.path.join(database_path, person)
    if os.path.isdir(person_path):
        for filename in os.listdir(person_path):
            img_path = os.path.join(person_path, filename)
            try:
                pil_image = Image.open(img_path).convert('RGB')
                img = np.array(pil_image)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    known_faces.append(encodings[0])
                    labels.append(i)
            except Exception as e:
                print(f"Erreur avec {img_path}: {e}")

# --- Initialisation ---
arduino = serial.Serial('COM16', 9600)
time.sleep(2)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Impossible d'ouvrir la webcam.")
    exit()

print("Système prêt. Appuyez sur 'q' pour quitter.")

last_sent = ""
last_sent_time = time.time()
repeat_interval = 3

def envoyer_arduino(msg):
    global last_sent, last_sent_time
    if msg != last_sent or (time.time() - last_sent_time > repeat_interval):
        arduino.write((msg + '\n').encode())
        print("Envoyé à Arduino:", msg)
        last_sent = msg
        last_sent_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    message_envoye = False

    if face_encodings:
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_faces, face_encoding)
            name = "Inconnu"

            if True in matches:
                face_distances = face_recognition.face_distance(known_faces, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = classes[labels[best_match_index]]

            if name != "Inconnu":
                envoyer_arduino(name)
                message_envoye = True
            else:
                envoyer_arduino("Inconnu")
                message_envoye = True
            break

    if not message_envoye:
        envoyer_arduino("NO_FACE")  # Affiche "QR code requis"

        # Vérifie présence QR code
        codes = decode(frame)
        for code in codes:
            data = code.data.decode('utf-8')
            print("QR Code détecté:", data)
            if data in qr_valides:
                envoyer_arduino("QR:" + data)
                time.sleep(1)
            else:
                envoyer_arduino("INVALID")
                time.sleep(1)

    # Affichage
    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow('Camera', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
