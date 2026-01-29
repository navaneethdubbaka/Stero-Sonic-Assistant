import requests

ESP32_IP = "10.145.69.134"  # Change to your ESP32 IP

def bulb_on():
    requests.get(f"http://{ESP32_IP}/lon")
    print("Bulb ON")

def bulb_off():
    requests.get(f"http://{ESP32_IP}/loff")
    print("Bulb OFF")
def socket_on():
    requests.get(f"http://{ESP32_IP}/son")
    print("Socket On")
def socket_off():
    requests.get(f"http://{ESP32_IP}/soff")
    print("Socket OFF")



while True:
    cmd = input("Enter ON / OFF / EXIT: ").lower()
    if cmd == "lon":
        bulb_on()
    elif cmd == "loff":
        bulb_off()
    elif cmd == "son":
        socket_on()
    elif cmd == "soff":
        socket_off()
    elif cmd == "exit":
        break
