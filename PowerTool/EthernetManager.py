from commonVariable import *
from sendSLDDCommand import slddCommand
from time import sleep

class EthernetManager():
    def __init__(self, deviceID = UNKNOWN_ID):
        self.slddCmd = slddCommand(deviceID)

    def setDeviceID(self, deviceID):
        self.slddCmd.setDeviceID(deviceID)
        self.ID = deviceID

    def isSendingTC10BoardReady(self):
        ret = E_ERROR
        isBootinCompleted = self.slddCmd.send_adb_shell_command("sldd am get_bootcomplete")
        if isBootinCompleted != None and isBootinCompleted != E_ERROR:
            if "1" in isBootinCompleted:
                ret = E_OK
        return ret

    def LoadPresettingConfig(self):
        print('Load Presetting')
        # if E_OK == self.isSendingTC10BoardReady():
        #     self.slddCmd.send_adb_shell_command("smack_admin")
        #     self.slddCmd.send_adb_shell_command("smack-profiler -p enable")
        #     self.slddCmd.send_adb_shell_command("Exit")
        self.slddCmd.send_adb_shell_command("systemctl stop ethernetManager.service")
        self.slddCmd.send_adb_shell_command("ifconfig bridge0 192.168.225.100")
        self.slddCmd.send_adb_shell_command("ifconfig bridge0 hw ether 00:55:7b:b5:7f:ff")

    def sendTC10On(self):
        print('sending TC10 On')
        if E_OK == self.isSendingTC10BoardReady():
            self.LoadPresettingConfig()
            self.slddCmd.send_adb_shell_command("echo reset > /sys/kernel/bcm89884/phy_reset")
            self.slddCmd.send_adb_shell_command("echo init > /sys/kernel/bcm89884/tc10_simulate")
        else:
            print("ERROR: Device is not found or booting is not completed")

    def sendTC10Off(self):
        print('sending TC10 Off')
        if E_OK == self.isSendingTC10BoardReady():
            self.LoadPresettingConfig()
            self.slddCmd.send_adb_shell_command("echo reset > /sys/kernel/bcm89884/phy_reset")
            self.slddCmd.send_adb_shell_command("echo init > /sys/kernel/bcm89884/tc10_simulate")
            self.slddCmd.send_adb_shell_command("echo sleep_req > /sys/kernel/bcm89884/tc10_simulate")
        else:
            print("ERROR: Device is not found or booting is not completed")

# cat /sys/class/net/eth0/operstate


    
