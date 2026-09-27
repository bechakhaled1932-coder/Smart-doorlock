import cv2
import serial
import time
from pyzbar.pyzbar import decode

# Connexion série avec Arduino sur COM16
arduino = serial.Serial('COM11', 9600, timeout=1)
time.sleep(2)  # Attente pour stabiliser la connexion

# Démarrage de la caméra
cap = cv2.VideoCapture(0)

print("En attente de QR Code valide...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    codes = decode(frame)
    for code in codes:
        data = code.data.decode('utf-8')
        print(f"QR Code détecté : {data}")

        if data == "khaled":
            print("Code valide détecté. Activation du relais.")
            arduino.write(b'ACTIVER\n')
            time.sleep(5)
            arduino.write(b'DESACTIVER\n')
            print("Relais désactivé. Prêt pour nouveau scan.")
            time.sleep(2)
        else:
            print("QR Code non valide.")

    cv2.imshow('Scanner QR', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
