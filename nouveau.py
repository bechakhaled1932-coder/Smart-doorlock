import serial
import time
import face_recognition
import cv2
import os
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# --- Paramètres ---
qr_valides = ["khaled"]
code_valide = "1234"
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
arduino = serial.Serial('COM16', 9600, timeout=1)
time.sleep(2)

repeat_interval = 3
countdown_time = 3  # secondes

def envoyer_arduino(msg):
    arduino.write((msg + '\n').encode('ascii'))
    if not msg.startswith("RELAIS_"):
        print("→ Arduino :", msg)

# --- Boucle principale ---
while True:
    print("En attente du choix du mode depuis l'Arduino...")
    mode = None

    while True:
        if arduino.in_waiting > 0:
            ligne = arduino.readline().decode('utf-8').strip()
            if ligne.startswith("MODE:"):
                mode = ligne.split(":")[1]
                print(f"Mode reçu : {mode}")
            elif ligne == "DETECTION:START" and mode in ['1', '2']:
                print("Déclenchement de la caméra...")
                break
            elif mode == '3' and ligne.startswith("CODE:"):
                user_code = ligne.split(":")[1]
                if user_code == code_valide:
                    envoyer_arduino("WELCOME:Code correct")
                    envoyer_arduino("RELAIS_ON")
                    time.sleep(3)
                    envoyer_arduino("RELAIS_OFF")
                else:
                    envoyer_arduino("ACCESS_DENIED")
                break

    # --- Démarrage caméra pour modes 1 ou 2 ---
    if mode in ['1', '2']:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Impossible d'ouvrir la webcam.")
            continue

        relais_active = False
        dernier_activation_time = 0

        print("Caméra active. Appuyez sur 'q' pour quitter.")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            name = "Inconnu"
            detection_valide = False

            if mode == '1':
                if face_encodings:
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(known_faces, face_encoding)
                        if True in matches:
                            face_distances = face_recognition.face_distance(known_faces, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = classes[labels[best_match_index]]
                                detection_valide = True
                        break

            elif mode == '2':
                codes = decode(frame)
                for code in codes:
                    data = code.data.decode('utf-8')
                    print("QR Code détecté:", data)
                    if data in qr_valides:
                        name = data
                        detection_valide = True
                    else:
                        envoyer_arduino("ACCESS_DENIED")
                        time.sleep(1)
                    break

            if detection_valide:
                envoyer_arduino(f"WELCOME:{name}")
                if not relais_active:
                    relais_active = True
                    dernier_activation_time = time.time()
            else:
                if mode == '1' and face_encodings:
                    envoyer_arduino("ACCESS_DENIED")

            if relais_active and (time.time() - dernier_activation_time > countdown_time):
                envoyer_arduino("RELAIS_OFF")
                relais_active = False

            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Fermeture de la caméra. Retour au choix du mode.")
                break

        cap.release()
        cv2.destroyAllWindows()
