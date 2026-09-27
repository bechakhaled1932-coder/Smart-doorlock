import serial
import time
import face_recognition
import cv2
import os
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# Chargement des visages connus
database_path = "C:\\Users\\Khaled\\Desktop\\CameraFaceRecognitionDoorLock\\known faces"
classes = os.listdir(database_path)

known_faces = []
labels = []

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

# Communication série
arduino = serial.Serial('COM16', 9600)
time.sleep(2)

# Caméra
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Impossible d'ouvrir la webcam.")
    exit()

print("Webcam active. Appuyez sur 'q' pour quitter.")

last_sent = ""
last_sent_time = 0
cooldown = 5  # secondes
waiting_for_qr = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        current_message = ""

        if face_encodings:
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_faces, face_encoding)
                name = "Inconnu"

                if True in matches:
                    face_distances = face_recognition.face_distance(known_faces, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = classes[labels[best_match_index]]

                current_message = name
                break

            if current_message != "Inconnu":
                if last_sent != current_message or (now - last_sent_time) > cooldown:
                    arduino.write((current_message + '\n').encode())
                    print(f"Visage reconnu : {current_message}")
                    last_sent = current_message
                    last_sent_time = now
                waiting_for_qr = False
            else:
                if last_sent != "Inconnu":
                    arduino.write(("Inconnu\n").encode())
                    print("Visage inconnu. Attente QR code...")
                    last_sent = "Inconnu"
                    last_sent_time = now
                waiting_for_qr = True
        else:
            if last_sent != "NO_FACE":
                arduino.write(("NO_FACE\n").encode())
                print("Aucun visage. Attente QR code...")
                last_sent = "NO_FACE"
                last_sent_time = now
            waiting_for_qr = True

        # Scan QR code si demandé
        if waiting_for_qr:
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                print("QR détecté : ", qr_data)

                if qr_data == "VALID_QR":
                    if last_sent != "QR_OK" or (now - last_sent_time) > cooldown:
                        arduino.write(("QR_OK\n").encode())
                        print("QR valide. Accès autorisé.")
                        last_sent = "QR_OK"
                        last_sent_time = now
                    waiting_for_qr = False
                else:
                    if last_sent != "QR_FAIL":
                        arduino.write(("QR_FAIL\n").encode())
                        print("QR invalide. Accès refusé.")
                        last_sent = "QR_FAIL"
                        last_sent_time = now
                    waiting_for_qr = False

        # Dessin sur l'image
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, current_message, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('Face Recognition', frame)

    except Exception as e:
        print("Erreur : ", e)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
