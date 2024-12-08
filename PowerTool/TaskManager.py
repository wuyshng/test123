from commonVariable import *
from sendSLDDCommand import slddCommand
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore
from time import sleep
from dltLib import DltClient
from testCaseData import testDatabase
from Log import Logger

class TaskManager(QtCore.QThread):
    signal = pyqtSignal(int)
    signalStr = pyqtSignal(str)
    def __init__(self, index = 0, deviceID = UNKNOWN_ID):
        super().__init__()
        self.index = index
        self.slddCmd = slddCommand(deviceID)
        self.dlt = DltClient()
        self.mtestDatabase = testDatabase()
        self.mLogMgr = Logger()
        self.TestCaseListEnabled = 0
        self.stopTesting = False
        self.testingDeviceID = deviceID
        self.numberOfTC = 0

    def updateTCInfor(self):
        for tc in range(TEST_CASE_START, self.numberOfTC):
            self.TestCaseListEnabled = self.TestCaseListEnabled | (1 << tc)


    def setNumberTC(self, numberOfTC):
        self.numberOfTC = numberOfTC
        self.updateTCInfor()

    def setDeivceID(self, deviceID):
        self.slddCmd.setDeviceID(deviceID)
        self.testingDeviceID = deviceID
        print(f"---------------> {self.slddCmd.testingDeviceID}")

    def enableTestCase(self, testCase, isEnabled):
        if (isEnabled == True):
            self.TestCaseListEnabled = self.TestCaseListEnabled | (1 << testCase)
            print (f"Enable test case: {testCase}")
        else:
            self.TestCaseListEnabled = self.TestCaseListEnabled & (~(1 << testCase))
            print (f"Disable test case: {testCase}")

        print(f"BitMask: {self.TestCaseListEnabled}")

    def isTestCaseEnable(self, testCase):
        print(self.TestCaseListEnabled)
        if ((self.TestCaseListEnabled & (1 << testCase)) == (1 << testCase)):
            print(f"TestCase {testCase} is enabled !!")
            return True
        else:
            print(f"TestCase {testCase} is NOT enabled !!")
            return False

    def run(self):
        self.stopTesting = False
        print("[Start to perform testing]")
        self.mLogMgr.clearLogs()
        self.signal.emit(SIGNAL_TESTING_STARTED)
        for testCaseID in range(TEST_CASE_START, self.numberOfTC):
            if (self.stopTesting == True): break
            if (self.isTestCaseEnable(testCaseID) == True):
                self.signal.emit(SIGNAL_START_WATCHDOG_TIMER)
                logMsg = (f"|----------=========>>> TestCaseID: [{testCaseID}] <<<=========-----------|\n")
                self.mLogMgr.Log(logMsg)
                self.signalStr.emit(logMsg)
                self.signal.emit(testCaseID)
                self.runTestCase(testCaseID)
                self.signal.emit(SIGNAL_STOP_WATCHDOG_TIMER)
                self.mLogMgr.Log("Start a WatchDog Timer")
                sleep(5)
            else:
                self.mLogMgr.Log(f"Test Case {testCaseID} is not enabled !")
        self.signal.emit(SIGNAL_TESTING_COMPLETED)
        self.mLogMgr.Log("___________________Testing is finished__________________")


    def runTestCase(self, testCaseID):
        testStep = LIST_TEST_STEP[testCaseID]
        for line in testStep:
            if (self.stopTesting == True): break

            [type, command] = line.split(",")
            type = type.strip()
            command = command.strip()
            logMsg = (f"|____________Test step_______: {type}")
            self.mLogMgr.Log(logMsg)
            self.signalStr.emit(logMsg)
            if (SEND_COMMAND == type):
                self.slddCmd.send_adb_shell_command(command)
                self.signalStr.emit(command)
                sleep(1)

            elif (RESET_BOARD == type):
                self.signal.emit(SIGNAL_RESET_BOARD)
                sleep(1)

            elif (WAIT_FOR_DEVICE_READY == type):
                self.waitForDevice()
                self.slddCmd.forwardLog()
                self.waitForBootComplete()

            elif (START_TO_GET_LOGS == type):
                self.dlt.start(self.mtestDatabase.getTCName(testCaseID))

            elif (WAIT_FOR_STATE_TRANSITION == type):
                print ("Waiting for state transition, duration:", int(command))
                sleep(int(command))   # Wait for state transition

            elif (STOP_CAN_NM == type):
                self.signal.emit(SIGNAL_STOP_CAN_NM)
                self.mLogMgr.Log("____________stopped_CanNM___________")
                sleep(10)

            elif (SEND_CAN_NM == type):
                self.signal.emit(SIGNAL_SEND_CAN_NM)
                self.mLogMgr.Log("____________sent_CanNM______________")

            elif (SEND_TC10_OFF == type):
                self.signal.emit(SIGNAL_SEND_TC10_OFF)
                self.mLogMgr.Log("____________Send TC10 OFF___________")
                sleep(10)

            elif (SEND_TC10_ON == type):
                self.signal.emit(SIGNAL_SEND_TC10_ON)
                self.mLogMgr.Log("____________Send TC10 ON______________")

            elif (REMOVE_VBAT == type):
                self.signal.emit(SIGNAL_REMOVE_VBAT)

            elif (VERIFY_LOG == type):
                sleep(10)
                self.dlt.stop()
                self.signal.emit(SIGNAL_VERIFY_LOGS)
                self.mLogMgr.Log("____________verified_Logs___________")
                sleep(5)
            elif (VERIFY_ADB_OUTPUT == type):
                self.mLogMgr.Log("____________verified_Adb_Outputs___________")
                expectedOutput = LIST_EXPECTED_RESULT[testCaseID][0]
                print(f"expected Result: {testCaseID} --> {expectedOutput}")
                ret = self.slddCmd.verifyADBOutput(command, expectedOutput)
                if (E_OK == ret):
                    self.signal.emit(SIGNAL_VERIFY_ADB_OUTPUT_VALID)
                else:
                    self.signal.emit(SIGNAL_VERIFY_ADB_OUTPUT_INVALID)

    def waitForDevice(self):
        if self.testingDeviceID == UNKNOWN_ID:
            while True:
                if (self.stopTesting == True): break
                deviceID = self.slddCmd.getDeviceID()
                if deviceID == E_ERROR:
                    # print(" Device is not ready to connect")
                    deviceID = self.slddCmd.getDeviceID()
                else:
                    self.mLogMgr.Log("Device is ready !!!")
                    break
                sleep(1)
        else:
            listDevice = self.slddCmd.getListDeviceID()
            while True:
                listDevice = self.slddCmd.getListDeviceID()
                if self.testingDeviceID in listDevice:
                    self.mLogMgr.Log(f"Device {self.testingDeviceID} is ready !!!")
                    break
                else:
                    print(f" Device {self.testingDeviceID} is not ready to connect")
                sleep(1)

    def waitForBootComplete(self):
        while (self.stopTesting == False):
            bootComplete = self.slddCmd.send_adb_shell_command("sldd am get_bootcomplete")
            if bootComplete != None and bootComplete != E_ERROR:
                if "1" in bootComplete:
                    self.mLogMgr.Log("Finished waiting for device ready")
                    break
            sleep(1)
        self.mLogMgr.Log("BootCompleted !!!")
        # self.slddCmd.send_adb_shell_command("sldd cfg setConfigData provisioneddata VcmLoggingOnOff 1")

    def cleanService(self):
        service = ["LocationManagerService", "AntennaManagerService"]
        for name in service:
            pid = self.slddCmd.getProcessID(name)
            print(pid)
            self.slddCmd.send_adb_shell_command(f"kill {pid}")

    def resetVCMBoardSetting(self):
        VCMSettingDefault = [
            "sldd OperationMode setOperationModeExt 0"
            "sldd cfg setConfigData ProvisionedData PwmInitialReceiveTime 86400"
            "sldd cfg setConfigData ProvisionedData PwmSleepTime 14400"
            "sldd cfg setConfigData ProvisionedData PwmReceiveTime 120"
            "sldd cfg setConfigData ProvisionedData PwmFirstPeriodicCycle 518400"
            "sldd power setprop_int pm.pwm.initial_started.time 0"
            "sldd power setprop_int pm.pwm.cycle.started.time 0"
        ]
        for command in VCMSettingDefault:
            self.slddCmd.send_adb_shell_command(command)

    def stop(self):
        self.finished.emit()
        self.stopTesting = True
        self.mLogMgr.Log("Stopped thread...")
        self.exit()