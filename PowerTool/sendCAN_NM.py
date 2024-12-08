# Import CANoe module. Always do this in your root script.
from py_canoe import CANoe
from time import sleep
from loadCanConfig import loadCANConfiguration
import pywintypes
from commonVariable import *
# create CANoe object. arguments are optional. Avoid creating multiple CANoe instances.

class CANHelper:

    def __init__(self):
        self.canBusState = CAN_BUS_UNKOWN

    def init(self):
        self.canoe_inst = CANoe()
        loadWorker = loadCANConfiguration()
        self.mcanoe_cfg = loadWorker.open_file_dialog()
        if (self.mcanoe_cfg == None):
            print("Error occurred while loading CAN Configuration")
            return False
        else:
            print(self.mcanoe_cfg)
            try:
                self.canoe_inst.open(canoe_cfg=self.mcanoe_cfg, visible=False, auto_save=False, prompt_user=False)
                self.setCanBusState(CAN_BUS_READY)
            except Exception as e:
                print('Error occurred while loading CAN Configuration: ' + str(e))

    def setCanBusState(self, newState):
        self.canBusState = newState

    def getCanBusState(self):
        return self.canBusState

    def sendCAN_NM(self):
        try:
            self.canoe_inst.start_measurement()
            self.canoe_inst.get_canoe_version_info()
            return E_OK
        except pywintypes.com_error as e:
            print("Error:", e)
            return E_ERROR

    def getCANoeInfor(self):
        try:
            version_info = self.canoe_inst.get_canoe_version_info()
            return version_info

        except pywintypes.com_error as e:
            print("Error:", e)
            return NO_VERSION

    def stopCAN_NM(self):
        self.canoe_inst.stop_measurement()

if __name__ == '__main__':
    canInstance = CANHelper()
    canInstance.init()
    canInstance.sendCAN_NM()
    sleep(10)
    canInstance.stopCAN_NM()





