from commonVariable import *
from sendSLDDCommand import slddCommand
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore
from time import sleep

class deviceMonitor(QtCore.QThread):
    signal = pyqtSignal(int)

    def __init__(self, index = 0, deviceID = UNKNOWN_ID):
        super().__init__()
        self.index = index
        self.slddCmd = slddCommand(deviceID)
        self.testingDeviceID = deviceID

    def setDeviceID(self, deviceID):
        self.slddCmd.setDeviceID(deviceID)
        self.testingDeviceID = deviceID
        print(f"deviceMonitor---------------> {self.slddCmd.testingDeviceID}")

    def run(self):
        print('Starting thread to monitor Device status', self.index)
        while True:
            deviceStatus = SIGNAL_DEVICE_DISCONNECTED
            deviceID = E_ERROR
            if (self.testingDeviceID == UNKNOWN_ID):
                deviceID = self.slddCmd.getDeviceID()
            else:
                listDevice = self.slddCmd.getListDeviceID()
                if self.testingDeviceID in listDevice:
                    deviceID = E_OK
            if deviceID != E_ERROR:
                isBootinCompleted = self.slddCmd.send_adb_shell_command("sldd am get_bootcomplete")
                if isBootinCompleted != None and isBootinCompleted != E_ERROR:
                    if "1" in isBootinCompleted:
                        deviceStatus = SIGNAL_DEVICE_BOOT_COMPLETED
                    else:
                        deviceStatus = SIGNAL_DEVICE_BOOTING
            self.signal.emit(deviceStatus)
            sleep(1)

    def stop(self):
        print('Stopping thread...', self.index)