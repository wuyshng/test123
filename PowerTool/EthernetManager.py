from commonVariable import *
from sendSLDDCommand import slddCommand
from time import sleep
import subprocess

class EthernetManager():
    def __init__(self, ID = UNKNOWN_ID):
        self.slddCmd = slddCommand(ID)
        self.TC10Method = METHOD_UNKNOWN
        self.deviceID = UNKNOWN_ID
        self.RadMoonID = UNKNOWN_ID

    def setMethodSendingTC10(self, method):
        self.TC10Method = method

    def setRADMoonID(self, ID):
        self.RadMoonID = ID

    def setDeviceID(self, ID):
        self.slddCmd.setDeviceID(ID)
        self.deviceID = ID

    def isSendingTC10BoardReady(self):
        ret = E_ERROR
        if (UNKNOWN_ID != self.deviceID):
            isBootinCompleted = self.slddCmd.send_adb_shell_command("sldd am get_bootcomplete")
            if isBootinCompleted != None and isBootinCompleted != E_ERROR:
                if "1" in isBootinCompleted:
                    ret = E_OK
        return ret
    
    def sendSignalByRadMoon(self, type):
        command = ""
        if (RM_CHECK_STATUS == type):
            command = f".\Radmoon2_TC10\status.exe {self.RadMoonID}"
        elif (RM_WAKE_TC10 == type):
            command = f".\Radmoon2_TC10\wake-mdio.exe {self.RadMoonID}"
        elif (RM_SLEEP_TC10 == type):
            command = f".\Radmoon2_TC10\sleep-mdio.exe {self.RadMoonID}"
        else:
            print('Failed type')
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if process.returncode == 0:
            if output:
                print(output.decode())
                return output.decode()
        else:
            print(f"Error executing command '{command}'.")
            if error:
                print("Error message:")
                print(error.decode())
                return E_ERROR

    def LoadPresettingConfig(self):
        print('Load Presetting')
        self.slddCmd.send_adb_shell_command("systemctl stop ethernetManager.service")
        self.slddCmd.send_adb_shell_command("ifconfig bridge0 192.168.225.100")
        self.slddCmd.send_adb_shell_command("ifconfig bridge0 hw ether 00:55:7b:b5:7f:ff")

    def sendTC10On(self):
        print('sending TC10 On')
        if (METHOD_RADMOON == self.TC10Method):
            if (self.sendSignalByRadMoon(RM_WAKE_TC10) != E_ERROR):
                print("SEND WAKE SIGNAL OK")
            else:
                print("SEND WAKE SIGNAL FAILED")
        else:
            if E_OK == self.isSendingTC10BoardReady():
                self.LoadPresettingConfig()
                self.slddCmd.send_adb_shell_command("echo reset > /sys/kernel/bcm89884/phy_reset")
                self.slddCmd.send_adb_shell_command("echo init > /sys/kernel/bcm89884/tc10_simulate")
            else:
                print("ERROR: Device is not found or booting is not completed")

    def sendTC10Off(self):
        print('sending TC10 Off')
        if (METHOD_RADMOON == self.TC10Method):
            if (self.sendSignalByRadMoon(RM_SLEEP_TC10) != E_ERROR):
                print("SEND SLEEP SIGNAL OK")
            else:
                print("SEND SLEEP SIGNAL FAILED")
        else:
            if E_OK == self.isSendingTC10BoardReady():
                self.LoadPresettingConfig()
                self.slddCmd.send_adb_shell_command("echo reset > /sys/kernel/bcm89884/phy_reset")
                self.slddCmd.send_adb_shell_command("echo init > /sys/kernel/bcm89884/tc10_simulate")
                self.slddCmd.send_adb_shell_command("echo sleep_req > /sys/kernel/bcm89884/tc10_simulate")
            else:
                print("ERROR: Device is not found or booting is not completed")
