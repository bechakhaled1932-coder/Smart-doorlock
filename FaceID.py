import face_recognition
import cv2
import os
import time

# Charger les visages connus
known_encodings = []
known_names = []

for file in os.listdir("known_faces"):
    img = face_recognition.load_image_file(f"known_faces/{file}")
    encoding = face_recognition.face_encodings(img)[0]
    known_encodings.append(encoding)
    known_names.append(os.path.splitext(file)[0])

# Initialiser la caméra
video = cv2.VideoCapture(0)

print("[INFO] Début de la reconnaissance faciale...")

while True:
    ret, frame = video.read()
    if not ret:
        break

    # Réduire la taille pour accélérer
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Localiser les visages
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    for encoding, location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, encoding)
        name = "Inconnu"

        if True in matches:
            match_index = matches.index(True)
            name = known_names[match_index]
            print(f"[INFO] Visage reconnu : {name}")
            time.sleep(2)  # Simule l'action d'un relais
        
        # Afficher le résultat
        top, right, bottom, left = [v * 4 for v in location]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.imshow("Face ID", frame)
    if cv2.waitKey(1) == 27:  # ESC pour quitter
        break

video.release()
cv2.destroyAllWindows()
