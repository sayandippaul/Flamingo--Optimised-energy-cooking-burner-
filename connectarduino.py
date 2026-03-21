import serial

try:
    s = serial.Serial("COM3", 9600)
    print("SUCCESS: Port opened")
    s.close()
except Exception as e:
    print("ERROR:", e)
