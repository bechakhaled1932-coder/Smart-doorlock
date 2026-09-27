import serial
import time
import face_recognition
import cv2
import os
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# --- Paramètres ---
face_timeout = 5  # secondes
database_path = "C:\\Users\\Khaled\\Desktop\\CameraFaceRecognitionDoorLock\\known faces"

# --- Dictionnaires de correspondance ---
codes_valides = {
    "2003": "khaled",
    "7890": "Mouadh",
    "1234": "Iyed"
}

qr_valides = {
    "khaled_qr": "khaled",
    "mouadh_qr": "Mouadh",
    "iyed_qr": "Iyed"
}

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

# --- Initialisation Arduino ---
arduino = serial.Serial('COM16', 9600, timeout=1)
time.sleep(2)

def envoyer_arduino(msg):
    arduino.write((msg + '\n').encode('ascii'))

def attendre_mode():
    while True:
        if arduino.in_waiting > 0:
            ligne = arduino.readline().decode('utf-8').strip()
            if ligne.startswith("MODE:"):
                return ligne.split(":")[1]

def attendre_detection_start():
    while True:
        if arduino.in_waiting > 0:
            ligne = arduino.readline().decode('utf-8').strip()
            if ligne == "DETECTION:START":
                return

# --- Boucle principale ---
while True:
    mode = attendre_mode()

    if mode in ['1', '2']:  # Mode reconnaissance faciale ou QR code
        attendre_detection_start()
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            continue

        relais_active = False
        dernier_activation_time = 0
        countdown_time = 3

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("→ Caméra fermée ou inaccessible")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            nom = "Inconnu"
            detection_valide = False

            if mode == '1' and face_encodings:
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_faces, face_encoding)
                    if True in matches:
                        face_distances = face_recognition.face_distance(known_faces, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            nom = classes[labels[best_match_index]]
                            detection_valide = True
                    break

            elif mode == '2':
                codes = decode(frame)
                for code in codes:
                    data = code.data.decode('utf-8')
                    print("QR détecté:", data)
                    if data in qr_valides:
                        nom = qr_valides[data]
                        detection_valide = True
                    else:
                        envoyer_arduino("ACCESS_DENIED")
                        time.sleep(1)
                    break

            if detection_valide:
                envoyer_arduino(f"WELCOME:{nom}")
                if not relais_active:
                    envoyer_arduino("RELAIS_ON")
                    relais_active = True
                    dernier_activation_time = time.time()

            if relais_active and (time.time() - dernier_activation_time > countdown_time):
                envoyer_arduino("RELAIS_OFF")
                relais_active = False

            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, nom, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow('Camera', frame)

            if cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1:
                print("→ Fenêtre fermée par l'utilisateur")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("→ Retour au choix du mode")
                break

        cap.release()
        cv2.destroyAllWindows()
        envoyer_arduino("RELAIS_OFF")  # Sécurité
        continue  # Retour à l'attente de choix de mode

    elif mode == '3':  # Clavier
        print("→ Mode clavier activé")
        while True:
            if arduino.in_waiting > 0:
                ligne = arduino.readline().decode('utf-8').strip()
                if ligne.startswith("CODE:"):
                    code_recu = ligne.split(":")[1]
                    if code_recu in codes_valides:
                        nom = codes_valides[code_recu]
                        envoyer_arduino(f"WELCOME:{nom}")
                        envoyer_arduino("RELAIS_ON")
                        time.sleep(3)
                        envoyer_arduino("RELAIS_OFF")
                    else:
                        envoyer_arduino("ACCESS_DENIED")
                elif ligne.startswith("MODE:"):
                    break  # Revenir au choix du mode
