import cv2
import serial
import time
from pyzbar.pyzbar import decode

# Connexion série avec Arduino sur COM16
try:
    arduino = serial.Serial('COM11', 9600, timeout=1)
    print("Connexion série établie.")
except serial.SerialException as e:
    print(f"Erreur de connexion série : {e}")
    exit()

# Démarrage de la caméra
cap = cv2.VideoCapture(0)

# Liste des QR codes valides
qr_valides = ["khaled"]
# Variable pour vérifier si un message a déjà été envoyé
message_envoye = False

# Variables pour temporisation
temps_attente_5s = 0  # Temps de démarrage de l'attente de 5 secondes
temps_attente_2s = 0  # Temps de démarrage de l'attente de 2 secondes
attente_5s_active = False  # Indicateur pour la temporisation de 5 secondes
attente_2s_active = False  # Indicateur pour la temporisation de 2 secondes

print("En attente de QR Code valide...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    codes = decode(frame)
    if len(codes) == 0:  # Si aucun QR code n'est détecté
        try:
            arduino.write(b'SCANNER\n')  # Demander à l'Arduino d'afficher "Scanner un QR..."
        except serial.SerialException as e:
            print(f"Erreur d'écriture série : {e}")

    for code in codes:
        data = code.data.decode('utf-8')
        print(f"QR Code détecté : {data}")

        if data in qr_valides and not message_envoye:  # Si QR valide et message non envoyé
            print("Code valide détecté.")
            try:
                # Envoi du message avec un retour à la ligne
                arduino.write(f"QR:{data}\n".encode())  
                arduino.write(b'RESET\n')  # Réinitialisation de l'affichage
                message_envoye = True  # Marquer que le message a été envoyé
                print("Affichage réinitialisé. Prêt pour un nouveau scan.")
                temps_attente_5s = time.time()  # Démarrer la temporisation de 5 secondes
                attente_5s_active = True  # Activer la temporisation de 5 secondes
            except serial.SerialException as e:
                print(f"Erreur d'écriture série : {e}")

        elif data not in qr_valides and not attente_2s_active:
            print("QR Code non valide.")
            try:
                arduino.write(b'INVALID\n')  # Message pour QR code invalide
                arduino.write(b'RESET\n')  # Réinitialisation de l'affichage
                attente_2s_active = True  # Activer la temporisation de 2 secondes
                temps_attente_2s = time.time()  # Démarrer la temporisation de 2 secondes
            except serial.SerialException as e:
                print(f"Erreur d'écriture série : {e}")

    # Vérifier la temporisation de 5 secondes
    if attente_5s_active and (time.time() - temps_attente_5s >= 5):
        print("Temps de 5 secondes écoulé, prêt pour un nouveau scan.")
        attente_5s_active = False  # Désactiver la temporisation de 5 secondes
        message_envoye = False  # Réinitialiser l'état du message envoyé

    # Vérifier la temporisation de 2 secondes
    if attente_2s_active and (time.time() - temps_attente_2s >= 2):
        print("Temps de 2 secondes écoulé, réinitialisation.")
        attente_2s_active = False  # Désactiver la temporisation de 2 secondes

    # Affichage de la caméra
    cv2.imshow('Scanner QR', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
