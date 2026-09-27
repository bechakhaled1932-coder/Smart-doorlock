import serial
import time
import face_recognition
import cv2
import os
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# Définir le chemin de la base de données
database_path = "C:\\Users\\Khaled\\Desktop\\CameraFaceRecognitionDoorLock\\known faces"
classes = os.listdir(database_path)

# Initialiser les listes pour les visages connus et les labels
known_faces = []
labels = []

# Charger les visages de la base de données
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
                else:
                    print(f"Aucun visage détecté dans {img_path}")
            except Exception as e:
                print(f"Erreur avec {img_path}: {e}")

# Initialiser la communication série avec l'Arduino
arduino = serial.Serial('COM16', 9600)
time.sleep(2)  # Attendre l'initialisation du port série

# Initialiser la caméra
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Impossible d'ouvrir la webcam.")
    exit()

print("Webcam démarrée. Appuyez sur 'q' pour quitter.")

# Fonction pour afficher les messages à l'utilisateur via l'écran LCD (envoi vers Arduino)
def afficher_message(message):
    arduino.write((message + '\n').encode())
    print(f"Message envoyé à Arduino : {message}")

# Fonction pour demander un code via le clavier (si QR Code échoue)
def demander_code():
    code_saisi = ""
    while len(code_saisi) < 4:  # Limiter à un code de 4 chiffres
        key = input("Entrez votre code PIN (4 chiffres) : ")
        if key.isdigit() and len(key) == 1:
            code_saisi += key
            print("*", end='', flush=True)  # Afficher * au lieu du chiffre
        if len(code_saisi) == 4:
            break
    return code_saisi

# Fonction pour vérifier si '*' est pressé sur le clavier matriciel (ici on le simule par un input)
def attendre_etoile():
    key = input("Appuyez sur '*' pour activer le relais : ")
    if key == "*":
        return True
    return False

last_sent = ""  # Dernier message envoyé
last_sent_time = time.time()
repeat_interval = 3  # Répéter l'envoi toutes les 3 secondes si le message reste le même

while True:
    ret, frame = cap.read()
    if not ret:
        print("Impossible de lire la frame.")
        break

    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        current_message = ""

        # Si des visages sont détectés
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
                break  # Traiter un seul visage à la fois

        # Si aucun visage n'est trouvé, tenter de détecter un QR code
        if current_message == "":
            qr_codes = decode(frame)
            if qr_codes:
                for qr in qr_codes:
                    qr_data = qr.data.decode('utf-8')  # Récupérer les données du QR code
                    current_message =  qr_data  # Mettre le nom du détenteur du QR code
            else:
                current_message = "NO_FACE"  # Aucun visage détecté et pas de QR code

        # Si aucun visage et QR code, demander un code via le clavier matriciel
        if current_message == "NO_FACE":
            print("Aucun visage détecté, veuillez entrer un code PIN.")
            code_saisi = demander_code()
            if code_saisi == "2003":  # Code PIN correct
                current_message = "PIN_VALID"

        # Attendre que l'utilisateur appuie sur '*' pour activer le relais
        if current_message != "" and attendre_etoile():
            afficher_message(current_message)
            print("Relais activé et message envoyé à Arduino :", current_message)

        # Afficher le cadre sur la vidéo
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, current_message, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('Face and QR Code Recognition', frame)

    except Exception as e:
        print(f"Erreur pendant la détection : {e}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Nettoyage
cap.release()
cv2.destroyAllWindows()
arduino.close()
