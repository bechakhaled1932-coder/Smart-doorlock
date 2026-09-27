import cv2
from pyzbar.pyzbar import decode
import numpy as np  # Importation de numpy pour la gestion des tableaux

# Initialiser la capture vidéo de la caméra
cap = cv2.VideoCapture(0)  # Utilisation de la première caméra disponible

if not cap.isOpened():
    print("Erreur: Impossible d'ouvrir la caméra.")
    exit()

while True:
    # Capturer chaque frame de la vidéo
    ret, frame = cap.read()
    if not ret:
        print("Erreur: Impossible de lire une image.")
        break

    # Décoder les QR codes dans l'image
    qr_codes = decode(frame)

    # Vérifier si des QR codes ont été détectés
    if qr_codes:
        for qr_code in qr_codes:
            qr_data = qr_code.data.decode('utf-8')  # Décoder les données du QR code
            print(f"Contenu du QR code : {qr_data}")  # Afficher le contenu du QR code

            # Dessiner un rectangle autour du QR code dans l'image pour le visualiser
            rect_points = qr_code.polygon
            if len(rect_points) == 4:
                pts = [tuple(point) for point in rect_points]
                pts = np.array(pts, dtype=np.int32)  # Utiliser numpy pour manipuler les points
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

            # Afficher le texte du QR code sur l'image
            x, y, w, h = qr_code.rect
            cv2.putText(frame, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Afficher l'image avec les QR codes détectés
    cv2.imshow("QR Code Scanner", frame)

    # Quitter la boucle si l'utilisateur appuie sur 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libérer les ressources et fermer les fenêtres
cap.release()
cv2.destroyAllWindows()
