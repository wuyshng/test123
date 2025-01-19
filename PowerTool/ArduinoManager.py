import serial
from time import sleep
from commonVariable import *

class ArduinoManager():
    def __init__(self, COMport):
        self.ser = serial.Serial(port = COMport, baudrate=9600, bytesize=8, timeout=5, stopbits=serial.STOPBITS_ONE)
        sleep(2)

    def __del__(self):
        self.ser.close()

    def sendCommandRequest(self, cmdRequest):
        if self.ser.is_open:
            print(f"Serial port {self.ser.name} is open")
        try:
            # Send a message to the Arduino
            if cmdRequest == TCUA_VBAT_ON:
                self.ser.write(b"\nTCUA_VBAT_ON\n")
                print("________________REQUEST TCUA_VBAT_ON: OK_____________________\n")

            elif cmdRequest == TCUA_VBAT_OFF:
                self.ser.write(b"\nTCUA_VBAT_OFF\n")
                print("________________REQUEST TCUA_VBAT_OFF: OK____________________\n")

            elif cmdRequest == VCM_VBAT_ON:
                self.ser.write(b"\nVCM_VBAT_ON\n")
                print("________________REQUEST VCM_VBAT_ON: OK_____________________\n")

            elif cmdRequest == VCM_VBAT_OFF:
                self.ser.write(b"\nVCM_VBAT_OFF\n")
                print("________________REQUEST VCM_VBAT_OFF: OK____________________\n")

            elif cmdRequest == POWER_RESET:
                self.ser.write(b"\nPOWER_RESET\n")
                print("________________REQUEST POWER_RESET: OK_________________\n")

            elif cmdRequest == CONNECT_ARDUINO:
                self.ser.write(b"\nCONNECT_ARDUINO\n")
                print("________________REQUEST CONNECT_ARDUINO: OK_____________\n")

            elif cmdRequest == BUB_ON:
                self.ser.write(b"\nBUB_ON\n")
                print("________________REQUEST BUB_ON: OK_____________________\n")

            elif cmdRequest == BUB_OFF:
                self.ser.write(b"\nBUB_OFF\n")
                print("________________REQUEST BUB_OFF: OK_____________________\n")

            elif cmdRequest == BOOT_ON:
                self.ser.write(b"\BOOT_ON\n")
                print("________________REQUEST BOOT_ON: OK_____________________\n")

            elif cmdRequest == BOOT_OFF:
                self.ser.write(b"\BOOT_OFF\n")
                print("________________REQUEST BOOT_OFF: OK_____________________\n")

            # Read and print the response from the Arduino
            response = self.ser.readline().decode('utf-8')
            print(f"Arduino responed: {response}")

        except serial.SerialException as e:
            print(f"Serial communication error: {e}")


if __name__ == '__main__':
    mArduinoManager = ArduinoManager("COM17")
    mArduinoManager.sendCommandRequest(TCUA_VBAT_ON)
    sleep(1)
    mArduinoManager.sendCommandRequest(TCUA_VBAT_OFF)
    sleep(1)
    mArduinoManager.sendCommandRequest(POWER_RESET)
    sleep(1)

    while True:
        cmd = input("Message: ")
        mArduinoManager.sendCommandRequest(cmd)
        print(cmd)

