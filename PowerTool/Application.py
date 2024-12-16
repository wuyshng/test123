
# Copyright (c) 2024 Your Company Name
# All rights reserved.
#
# \brief    This is TST Tool used for testing Tiger services
#
# \details
#    This software is copyright protected and proprietary to
#    LG electronics. LGE grants to you only those rights as
#    set out in the license conditions. All other rights remain
#    with LG electronics.
#
# \authors:
#    copyright (c) 2024  by Power Team
#    + Nguyen Xuan Thuong <thuong4.nguyen@lge.com>
#    + Ho Trieu Phu Danh  <danh.ho@lge.com>
#
# \attention Copyright (c) 2024 by LG electronics co, Ltd. All rights reserved.

import sys
import threading
from PyQt5.Qt import Qt
from toolGui import Ui_TestingTool
from sendSLDDCommand import slddCommand
from sendCAN_NM import CANHelper
from loadCanConfig import loadCANConfiguration
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox
from PyQt5 import QtCore, QtGui, QtWidgets # type: ignore
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QPushButton, QToolBar, QAction, QFileDialog
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from time import sleep
import time
import json
import re
import os
from datetime import datetime
from commonVariable import *
import serial.tools.list_ports
from robot.api.parsing import get_model
from testCaseData import testDatabase
from dltLib import DltClient
from deviceMonitor import deviceMonitor
from AutomateQFIL import AutomateQFIL

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QColor
from PyQt5 import QtCore
from TaskManager import TaskManager
from ArduinoManager import ArduinoManager
from EthernetManager import EthernetManager
from LoadRobotTestCase import LoadRobotTestCase
from RunRobotTestScript import RunRobotTestScript

def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

class UI_Power_tool(QObject, Ui_TestingTool):
# Init function =========================================================================
    def __init__(self, TestingTool):
        super().__init__()
        self.TestingTool = TestingTool
        self.mdeviceStatus = NOT_READY
        self.setupUi(TestingTool)
        self.setupButtonClickHander()
        self.mtestDatabase = testDatabase()
        self.setupCommandForMenu()
        self.mCANHelper = CANHelper()
        self.slddCmd = slddCommand()
        self.dlt = DltClient()
        self.countTestResult = 0
        self.countTestPassed = 0
        self.countTestFailed = 0
        self.totalTC = TEST_CASE_START
        self.TestResultDisplayer.setText(f"0/{self.totalTC}")
        self.progressBar.setProperty("value", self.countTestResult/self.totalTC)
        # self.setupTestCaseTable(self.totalTC)
        self.isDeviceMonitored = False
        self.mdeviceMonitor = deviceMonitor(index = 1001)
        self.mdeviceMonitor.signal.connect(self.onReceivedDeviceSignal)
        self.mTaskManager = TaskManager()
        self.mTaskManager.signal.connect(self.onReceivedEvent)
        self.mTaskManager.signalStr.connect(self.onReceivedDeviceSignalStr)
        self.testingOnGoing = False
        self.TestCaseEnabled = self.totalTC
        self.currentTestCase = 0
        self.startedTestTime = 0
        self.executedTime = 0
        self.ArduinoPort = NO_PORT_CONNECTED
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.displayAvailablePort)
        self.timer.start(1000)  # Update every 1 second
        self.watchDogTimer = QtCore.QTimer()
        self.watchDogTimer.timeout.connect(self.onTimerWatchDogTimerTimeout)
        self.initSlddList()
        self.startMonitoringDevice()
        self.VCMTimer = QtCore.QTimer()
        self.timer.timeout.connect(self.displayAvailableVCMBoard)
        self.timer.start(3000)  # Update every 1 second
        self.VCMListDevice = []
        self.VCMTestingBoardID = UNKNOWN_ID
        self.VCMSendingTC10BoardID = UNKNOWN_ID
        self.mEthernetManager = EthernetManager()
        # self.loadDefaultTestConfiguration()
        self.setupRobotTestCaseTable()
        self.mAutomateQFIL = AutomateQFIL()
        self.mAutomateQFIL.signal.connect(self.displayQFILInformation)
        self.mAutomateQFIL.progressSignal.connect(self.displayQFILProgress)
        self.mAutomateQFIL.defautDownloadURLSignal.connect(self.displayDefaultDonwloadURLSignal)
        self.testFileType = None
        self.boardName = "_".join(self.SWversionDisplayer.text().split("_")[:2])

# Delete function ======================================================================
    def __del__(self):
        print("_______________On Exit________________________")
        if self.mCANHelper.getCanBusState() == CAN_BUS_ACTIVE:
            self.mCANHelper.stopCAN_NM()

# Setup Button click handler ===========================================================
    def setupButtonClickHander(self):
        self.setupsendSLDDButton()
        self.setupConnectBoardButton()
        self.setupActiveCanBusButton()
        self.setupstartTaskButton()
        self.setupstopTaskButton()
        self.setupclearButton()
        self.setupPowerResetButton()
        self.setUpPowerButton()
        self.setUpKeepAliveButton()
        self.setUpLoggerButton()
        self.setUpAutoForwardLogButton()
        self.setUpTestingBoardConnectButton()
        self.setUpSendingTC10BoardConnectButton()
        self.setUpTC10OnButton()
        self.setUpTC10OffButton()
        self.setUpActionLoadTestCase()
        self.setUpActionLoadRobotTestCase()
        self.setUpStartFLButton()
        self.setUpStopFLButton()

# Setup Command for Menu bar ===========================================================
    def setupCommandForMenu(self):
        self.setupCommandOnMenuSelect()
        self.setUpSaveTestResult()


# Warnning functions ===================================================================
    def show_alert(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()


# Display board information =============================================================

    def onReceivedDeviceSignalStr(self, signalStr):
        self.Console.append(signalStr)

    def onReceivedDeviceSignal(self, signal):
        if signal == SIGNAL_DEVICE_BOOTING:
            self.setDeviceState(BOOTING)

        elif signal == SIGNAL_DEVICE_BOOT_COMPLETED:
            self.setDeviceState(NORMAL)

        elif signal == SIGNAL_DEVICE_DISCONNECTED:
            self.setDeviceState(DISCONNECTED)
            self.ConnectBoardButton.setEnabled(True)


    def startMonitoringDevice(self):
        if (self.isDeviceMonitored == False):
            self.isDeviceMonitored = True
        self.mdeviceMonitor.start()



    def connecToBoard(self):
        # Check if the board is booting complted
        deviceID = self.slddCmd.getDeviceID()
        if deviceID == E_ERROR:
            self.show_alert("Failed to connect Board", "Device is not active yet !")
            self.Console.setText(f"Device is not ready to connect, please try again after a few seconds ...")
        else:
            self.ConnectBoardButton.setEnabled(False)
            self.ConnectBoardButton.setText("Board connected")


    def displayBoardInformation(self):
        deviceID = self.slddCmd.getDeviceID()
        if deviceID == E_ERROR:
            self.Console.setText(f"DEVICE IS NOT ACTIVE")
        else:
            result = self.slddCmd.send_adb_shell_command(None)
            if result == E_ERROR:
                print("Failed to connect Board", "No devices/emulators found !")
            else:
                APversion = self.slddCmd.send_adb_shell_command("cat /etc/version")
                self.SWversionDisplayer.setText(APversion)
                MCUversion = self.slddCmd.send_adb_shell_command("ls /micom/")
                MCUversion = MCUversion[:-7]
                print(MCUversion)
                self.MCUVersionDispalyer.setText(MCUversion)
                cmdLineInfor = self.slddCmd.send_adb_shell_command("cat /proc/cmdline")
                cmdLineInforStr =  (rf"{cmdLineInfor}")
                HardwareVer = self.findHardwareVersion(cmdLineInforStr)
                self.HWVersionDisplayer.setText(HardwareVer)

    def displayAvailablePort(self):
        self.PowerSourceControl.clear()
        ports = serial.tools.list_ports.comports()
        # Print information about the devices connected to each COM port
        port_names = [port.device for port in ports]
        self.PowerSourceControl.addItems(port_names)
        self.ArduinoPort = NO_PORT_CONNECTED
        for port in ports:
            if "USB-SERIAL CH340" in port.description or "Arduino Uno" in port.description:
                self.ArduinoPort = f"{port.device}"
                # print(f"Arduino connected to Port: {self.ArduinoPort}")
                break
            else:
                self.ArduinoPort = NO_PORT_CONNECTED

        if self.ArduinoPort == NO_PORT_CONNECTED:
            self.ArduinoStatus.setText("Not Connected")
            self.PowerOnButton.setEnabled(True)
            self.ArduinoStatus.setStyleSheet("background-color: rgb(253, 255, 152);\n"
                                "border-color: rgb(253, 255, 152);")

# OnButton clicked settings =============================================================

    def setupsendSLDDButton(self):
        self.sendSLDDButton.clicked.connect(self.sendSlddCommandInput)

    def setupConnectBoardButton(self):
        self.ConnectBoardButton.clicked.connect(self.connecToBoard)

    def setupActiveCanBusButton(self):
        self.ActiveCanBusButton.clicked.connect(self.onCanButtonPress)

    def setupstartTaskButton(self):
        self.startTaskButton.clicked.connect(self.startTask)


    def setupstopTaskButton(self):
        self.stopTaskButton.clicked.connect(self.stopTest)

    def setupclearButton(self):
        self.clearButton.clicked.connect(self.onHandleClearButton)

    def setupPowerResetButton(self):
        self.PowerResetButton.clicked.connect(self.onHandlePowerReset)

    def setUpPowerButton(self):
        self.PowerOnButton.clicked.connect(self.handlePowerButtonPressed)

    def setUpKeepAliveButton(self):
        self.keepAliveButton.clicked.connect(self.handlekeepAliveButtonPressed)

    def setUpLoggerButton(self):
        self.enableLogButton.clicked.connect(self.handleEnableLoggerButton)

    def setUpAutoForwardLogButton(self):
        self.AutoForwardLogButton.toggled.connect(self.onAutoForwardLogButtonToggled)

    def setUpTestingBoardConnectButton(self):
        self.TestingBoardConnectButton.clicked.connect(self.onClickTestingBoardConnectButton)

    def setUpSendingTC10BoardConnectButton(self):
        self.SendingTC10BoardConnectButton.clicked.connect(self.onClickSendingTC10BoardConnectButton)

    def setUpTC10OnButton(self):
        self.TC10OnButton.clicked.connect(self.onClickTC10OnButton)

    def setUpTC10OffButton(self):
        self.TC10OffButton.clicked.connect(self.onClickTC10OffButton)

    def setUpActionLoadTestCase(self):
        self.actionLoad_json_test_cases.triggered.connect(self.loadConfigTestCase)

    def setUpActionLoadRobotTestCase(self):
        self.actionLoad_robot_test_cases.triggered.connect(self.loadRobotTestCase)

    def setUpStartFLButton(self):
        self.startFLButton.clicked.connect(self.startAutomateQFIL)

    def setUpStopFLButton(self):
        self.stopFLButton.clicked.connect(self.stopAutomateQFIL)

# Send sldd command sellected ===========================================================

    def sendSlddCommandInput(self):
        self.sendSlddCommand(self.slddList.currentText())

    def sendSlddCommand(self, cmd):
        slddCmd = slddCommand()
        result = slddCmd.send_adb_shell_command(cmd)
        if result == E_ERROR:
            self.Console.setText("Device is not found !!!")
        else:
            self.Console.setText(f"{result}\n")


# Download daily build image from Artifactory ===========================================
    def startAutomateQFIL(self):
        self.boardName = "_".join(self.SWversionDisplayer.text().split("_")[:2])
        self.mAutomateQFIL.boardName = self.boardName

        self.AutomateQFILAction()
        if self.mAutomateQFIL.runDownloadOnly == False and self.mAutomateQFIL.runFlashOnly == False:
            self.show_alert("Flash Loader", "Please select download or flash")
            return
        elif self.mAutomateQFIL.runDownloadOnly == True and self.mdeviceStatus != NORMAL:
            self.Console.setText("Not ready to download! Please check devices")
            return

        if self.downloadImgURL.text() != self.defaultDownloadURL:
            self.mAutomateQFIL.downloadFromURL = self.downloadImgURL.text()

        self.startFLButton.setEnabled(False)
        self.mAutomateQFIL.finished.connect(self.onAutomateQFILFinished)
        self.FLProgressBar.setProperty("value", 0)
        self.mAutomateQFIL.start()

    def onAutomateQFILFinished(self):
        self.mAutomateQFIL.stop()
        self.startFLButton.setEnabled(True)
        
    def displayQFILInformation(self, message):
        self.Console.setText(message)

    def displayQFILProgress(self, message):
        self.FLProgressBar.setProperty("value", message)

    def displayDefaultDonwloadURLSignal(self, message):
        self.downloadImgURL.setPlaceholderText(message)

    def AutomateQFILAction(self):
        self.mAutomateQFIL.runDownloadOnly = self.downloadImgButton.isChecked()
        self.mAutomateQFIL.runFlashOnly = self.flashImgButton.isChecked()
    
    def stopAutomateQFIL(self):
        self.mAutomateQFIL.stop()
        self.startFLButton.setEnabled(True)

# SetUp command when menu is sellected ==================================================
    def setupCommandOnMenuSelect(self):
        self.actionLoad_CAN_configuration.triggered.connect(self.setupCAN)

    def setUpSaveTestResult(self):
        self.actionSave_the_test_result.triggered.connect(self.exportTestResult)

# Functions handle CAN  =================================================================
    def setupCAN(self):
        self.Console.setText("CAN config is loading ...")
        if (self.mCANHelper.init() == False):
            self.show_alert("Failed to load CAN configuration", "please sellect CAN config")
        else:
            self.Console.setText("CAN config is loaded successfully !")
            version_info = self.mCANHelper.getCANoeInfor()
            if version_info == NO_VERSION:
                self.Console.setText("Can not get CANoe Information !")
            else:
                self.Console.append("CANoe Information:\n")
                for key, value in version_info.items():
                    infor = f"{key}:{value}"
                    self.Console.append(infor)

    def sendCanNM(self):
        if (CAN_BUS_ACTIVE != self.mCANHelper.getCanBusState()):
            ret = self.mCANHelper.sendCAN_NM()
            if ret == E_ERROR:
                print("Failed to send")
                self.show_alert("Failed to send CAN_NM", "No CANoe connected !")
            else:
                self.mCANHelper.setCanBusState(CAN_BUS_ACTIVE)
                self.onCanBusStateChanged(CAN_BUS_ACTIVE)
        else:
            print("[WARNING]: CAN BUS IS ALREADY ACTIVE !")

    def stopCanNM(self):
        if (CAN_BUS_ACTIVE == self.mCANHelper.getCanBusState()):
            ret = self.mCANHelper.stopCAN_NM()
            if ret == E_ERROR:
                print("Failed to stop")
                self.show_alert("Failed to stop send CAN_NM", "No CANoe connected !")
            else:
                self.mCANHelper.setCanBusState(CAN_BUS_SLEEP)
                self.onCanBusStateChanged(CAN_BUS_SLEEP)
        else:
            print("CAN BUS IS NOT ACTIVE !")

    def onCanButtonPress(self):
        if (self.mCANHelper.getCanBusState() == CAN_BUS_UNKOWN):
            # Init for the first time
            self.show_alert("Can config not available", "Please load CAN config first !")
            self.Console.setText("CAN config has not been loaded yet\n Sellect >> File -> Load CAN configuration")
        # Ready mean CAN config is loaded
        elif (self.mCANHelper.getCanBusState() == CAN_BUS_READY):
            self.sendCanNM()

        elif (self.mCANHelper.getCanBusState() == CAN_BUS_ACTIVE):    # Change CANBus state ACTIVE -> SLEEP
            self.stopCanNM()

        elif (self.mCANHelper.getCanBusState() == CAN_BUS_SLEEP):     # Change CANBus state SLEEP -> ACTIVE
            self.sendCanNM()
        else:
            print("INVALID STATE")

    def startTask(self):
        self.mdeviceStatus = NORMAL
        if (self.mdeviceStatus == NORMAL and self.testFileType is not None):
            self.countTestPassed = 0
            self.countTestFailed = 0
            self.progressBar.setProperty("value",  0)
            self.ledDisplayPassResult.setProperty("value", self.countTestPassed)
            self.ledDisplayFailedResult.setProperty("value", self.countTestFailed)
            self.TestResultDisplayer.setText(f"0/{self.TestCaseEnabled}")
            self.Console.setText("Testing is starting...")
            self.startTaskButton.setEnabled(False)
            self.ConnectBoardButton.setEnabled(False)
            self.startTaskButton.setEnabled(False)
            self.ActiveCanBusButton.setEnabled(False)
            self.AutoKeepAliveButton.setChecked(False)
            self.AutoForwardLogButton.setChecked(False)

            if self.testFileType == "json":
                self.mTaskManager.start()
            elif self.testFileType == "robot":
                selectedTests = self.getSelectedTestCases()
                if not selectedTests:
                    self.Console.setText("No test cases selected!")
                    self.startTaskButton.setEnabled(True)
                    return
                
                outputDir = "../output"
                self.mRunRobotTestScript = RunRobotTestScript(selectedTests, self.robotFilePath, outputDir, self.TestCaseTable)
                self.mRunRobotTestScript.testResultSignal.connect(self.updateRobotTestResult)
                self.mRunRobotTestScript.testProgressSignal.connect(self.notifyTestScriptProgress)
                self.mRunRobotTestScript.testCountSignal.connect(self.updateRobotTestCaseAmount)
                self.mRunRobotTestScript.logSignal.connect(self.displayRobotLog)
                self.mRunRobotTestScript.finishedSignal.connect(self.robotTestFinished)
                self.mRunRobotTestScript.start()
                self.Console.setText("Running tests ...")
            
            self.testingOnGoing = True

        elif self.mdeviceStatus == NORMAL and self.testFileType is None:
                self.show_alert("Failed to start task", "Please load test case")
                self.startTaskButton.setEnabled(True)
                return
        
        else:
            self.show_alert("Failed to start", "Devices is not ready to run Test !")
            self.Console.setText("Board is not ready to run Test ! \nPlease check devices (Board, Arduino) ...")
        
    
    def getSelectedTestCases(self):
        selectedTests = []
        currentFile = None

        for row in range(1, self.TestCaseTable.rowCount()):
            fileItem = self.TestCaseTable.item(row, 1)
            testCaseItem = self.TestCaseTable.item(row, 2)

            if fileItem and (not testCaseItem or testCaseItem.text().strip() == ""):
                currentFile = fileItem.text().replace(".robot", "").strip()
                continue

            checkboxItem = self.TestCaseTable.cellWidget(row, 0)
            if checkboxItem:
                checkbox = checkboxItem.findChild(QCheckBox)
                if checkbox and checkbox.isChecked() and currentFile and testCaseItem:
                    testCaseName = testCaseItem.text().strip()
                    if testCaseName:
                        selectedTests.append(f"{currentFile}.{testCaseName}")

        return selectedTests
    
    def updateRobotTestResult(self, testInfo):
        fileName, testName, testStatus = testInfo.split(":::")
        currentFileName = None

        for row in range(1, self.TestCaseTable.rowCount()):
            fileItem = self.TestCaseTable.item(row, 1)
            testItem = self.TestCaseTable.item(row, 2)

            if fileItem and (testItem is None or testItem.text().strip() == ""):
                currentFileName = fileItem.text().replace(".robot", "").strip()
                continue

            if (currentFileName == fileName and testItem and testItem.text().strip() == testName):
                self.setTestResult(row, testStatus)
                if testStatus == "PASS":
                    self.countTestPassed += 1
                    self.ledDisplayPassResult.setProperty("value", self.countTestPassed)
                elif testStatus == "FAIL":
                    self.countTestFailed += 1
                    self.ledDisplayFailedResult.setProperty("value", self.countTestFailed)
                break

    def notifyTestScriptProgress(self, message):
        self.Console.setText(message)

    def displayRobotLog(self, message):
        self.Console.append(message)

    def robotTestFinished(self, message):
        self.startTaskButton.setEnabled(True)
        self.Console.append(message)
        self.mRunRobotTestScript.exit()


    def onReceivedEvent(self, event):
        if (SIGNAL_SEND_CAN_NM == event):
            self.sendCanNM()

        elif (SIGNAL_STOP_CAN_NM == event):
            self.stopCanNM()

        elif (SIGNAL_SEND_TC10_OFF == event):
            self.onClickTC10OffButton()

        elif (SIGNAL_SEND_TC10_ON == event):
            self.onClickTC10OnButton()

        elif (SIGNAL_START_WATCHDOG_TIMER == event):
            self.watchDogTimer.start(600000)    # 600 seconds, If device is not respond/wakeup -> power reset
            print("Start watchdog timer with timeout = 600 sec")

        elif (SIGNAL_STOP_WATCHDOG_TIMER ==  event):
            self.watchDogTimer.stop()

        elif (SIGNAL_RESET_BOARD == event):
            self.onHandlePowerReset()

        elif (SIGNAL_REMOVE_VBAT == event):
            self.turnOffVBAT()

        elif (SIGNAL_VERIFY_LOGS == event):
            self.verifyLog(self.currentTestCase)

        elif (SIGNAL_TESTING_STARTED == event):
             self.executedTime = time.time()

        elif (SIGNAL_TESTING_COMPLETED == event):
            self.updateTotalExecutedTime()

        elif ((event >= TEST_CASE_START) and (event <= self.totalTC+1)):
            # Notify current TestCase
            self.currentTestCase = event
            self.startedTestTime = time.time()
        elif (SIGNAL_VERIFY_ADB_OUTPUT_VALID == event):
            self.verifyADBOutput(PASSED)
        elif (SIGNAL_VERIFY_ADB_OUTPUT_INVALID == event):
            self.verifyADBOutput(FAILED)

    def verifyADBOutput(self, result):
        self.countTestResult += 1
        self.updateTestCaseAmount()
        self.setTestResult(LIST_TC_POSITION[self.currentTestCase], result)
        self.updateExecutedTime(self.currentTestCase)
        if result == PASSED:
            self.countTestPassed += 1
            self.ledDisplayPassResult.setProperty("value", self.countTestPassed)
        else:
            self.countTestFailed += 1
            self.ledDisplayFailedResult.setProperty("value", self.countTestFailed)

    def verifyLog(self, testCaseID):
        print(f"verifyLog : {testCaseID}")
        self.countTestResult += 1
        self.updateTestCaseAmount()
        Logs = self.dlt.printMsg(self.mtestDatabase.getTCName(testCaseID, LIST_TC_NAME))
        print("==========[Print console Logs]==========")
        self.Console.append(f"{Logs}")
        self.updateTestResult(testCaseID)
        print("==========[END console Logs]============")
        sleep(2)


    def updateTestResult(self, testCaseID):
        print(f"UpdateTestResult : {testCaseID}")
        ret = True
        for index in range(0, len(LIST_EXPECTED_RESULT[testCaseID])):
            expected = LIST_EXPECTED_RESULT[testCaseID][index]
            position = LIST_TC_POSITION[testCaseID] + index
            result = self.dlt.isContainExpectedLog(expected, self.mtestDatabase.getTCName(testCaseID, LIST_TC_NAME))
            if result == True:
                self.setTestResult(position, PASSED)
            else:
                self.setTestResult(position, FAILED)
                ret = False
        self.updateExecutedTime(testCaseID)
        if ret == True:
                self.countTestPassed += 1
                self.ledDisplayPassResult.setProperty("value", self.countTestPassed)
        else:
            self.countTestFailed += 1
            self.ledDisplayFailedResult.setProperty("value", self.countTestFailed)

    def stopTest(self):
        if (self.testingOnGoing == True):
            self.Console.setText(f"STOPPED")
            self.startTaskButton.setEnabled(True)
            self.ActiveCanBusButton.setEnabled(True)
            self.mTaskManager.stop()
            self.mRunRobotTestScript.stop()
            self.testingOnGoing = False


# Handle CAN bus state changed events =====================================================
    def onCanBusStateChanged(self, state):
        if state == CAN_BUS_ACTIVE:
            self.ActiveCanBusButton.setText("Stop CAN")
            self.CANStatus.setText("Active")
            self.CANStatus.setStyleSheet("background-color: rgb(180, 255, 186);\n"
                                            "border-color: rgb(115, 172, 172);")
        elif state == CAN_BUS_SLEEP:
            self.ActiveCanBusButton.setText("Active CAN")
            self.CANStatus.setText("Sleep")
            self.CANStatus.setStyleSheet("background-color: rgb(253, 255, 152);\n"
                                            "border-color: rgb(253, 255, 152);")
        else:
            print("not Valid State")

# Handle Button clicked
    def onHandleClearButton(self):
        self.Console.clear()
        self.startTaskButton.setEnabled(True)
        self.ConnectBoardButton.setEnabled(True)
        self.countTestResult = 0
        self.countTestPassed = 0
        self.countTestFailed = 0
        self.progressBar.setProperty("value",  0)
        self.ledDisplayPassResult.setProperty("value", self.countTestPassed)
        self.ledDisplayFailedResult.setProperty("value", self.countTestFailed)
        if self.testFileType == "json":
            self.TestResultDisplayer.setText(f"0/{self.totalTC}")
        elif self.testFileType == "robot":
            self.TestResultDisplayer.setText(f"0/{self.TestCaseEnabled}")
        self.clearTestResult()

    def onHandlePowerReset(self):
        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(POWER_RESET)
        else:
            self.show_alert("Failed to connect", "COM ports are not available")

    def handlePowerButtonPressed(self):
        # Get a list of available COM ports
        ports = serial.tools.list_ports.comports()
        # Print information about the devices connected to each COM port
        for port in ports:
            print(f"Port: {port.device}")
            print(f"Description: {port.description}")
            if "USB-SERIAL CH340" in port.description or "Arduino Uno" in port.description:
                self.ArduinoPort = f"{port.device}"
                print(f"Arduino connected to Port: {self.ArduinoPort}")
                break
            
        if self.ArduinoPort != NO_PORT_CONNECTED:
            if (self.PowerOnButton.text() == "Power On"):
                self.Console.setText("Connecting to Arduino ...")
                mArduinomgr = ArduinoManager(self.ArduinoPort)
                mArduinomgr.sendCommandRequest(VBAT_OFF)
                mArduinomgr.sendCommandRequest(BUB_OFF)
                mArduinomgr.sendCommandRequest(VBAT_ON)
                self.PowerOnButton.setText("Power Off")
                self.ArduinoStatus.setText("Connected")
                self.ArduinoStatus.setStyleSheet("background-color: rgb(180, 255, 186);\n"
                                                "border-color: rgb(115, 172, 172);")
                self.Console.setText("Connected to Arduino sucessfully!")

            elif (self.PowerOnButton.text() == "Power Off"):
                mArduinomgr = ArduinoManager(self.ArduinoPort)
                mArduinomgr.sendCommandRequest(VBAT_OFF)
                self.PowerOnButton.setText("Power On")
                self.ArduinoStatus.setText("Disconnected")
                self.ArduinoStatus.setStyleSheet("background-color: rgb(253, 255, 152);\n"
                                                "border-color: rgb(253, 255, 152);")
                self.ArduinoPort = NO_PORT_CONNECTED
                self.Console.setText("Disconnected to Arduino sucessfully!")
            print("SEND ME")

        else:
            self.show_alert("Failed to connect", "Arduino port is not available")

    def handlekeepAliveButtonPressed(self):
        if (self.getDeviceState() == NORMAL):
            self.keepBoardAlive()
            self.Console.setText("Request keepAlive sucessfully!")
        else: self.show_alert("Failed to request", "Device is not ready")

    def handleEnableLoggerButton(self):
        if (self.getDeviceState() == NORMAL):
            self.slddCmd.forwardLog()
            self.Console.setText("Forward logs sucessfully !")
        else: self.show_alert("Failed to request", "Device is not ready")


    def onAutoForwardLogButtonToggled(self):
        if (self.getDeviceState() == NORMAL):
            self.slddCmd.forwardLog()
            self.Console.setText("Auto forward-logs is enabled sucessfully !")
        else: self.show_alert("Failed to request", "Device is not ready")

# Setup Test case tables
    def setupTestCaseTable(self, totalRow = 0):
        self.TestCaseTable.clear()
        self.TestCaseTable.setColumnCount(6)
        self.TestCaseTable.setRowCount(totalRow + 1) # + 1 for Test Case All
        print(f"total Testcases = {self.totalTC}")
        self.TestCaseTable.setHorizontalHeaderLabels(["Select","Test Case", "Description", "Expected logs result", "Test Result", " Executed Time"])

        header = self.TestCaseTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: lightblue; font-size: 12pt; }")
        vheader = self.TestCaseTable.verticalHeader()
        vheader.setStyleSheet("QHeaderView::section { font-size: 12pt; }")
        self.TestCaseTable.verticalHeader().setVisible(False)

        self.TestCaseTable.setColumnWidth(0, 70)
        self.TestCaseTable.setColumnWidth(1, 140)
        self.TestCaseTable.setColumnWidth(2, 750)
        self.TestCaseTable.setColumnWidth(3, 470)
        self.TestCaseTable.setColumnWidth(4, 200)
        self.TestCaseTable.setColumnWidth(5, 200)
        self.TestCaseTable.setStyleSheet("gridline-color: rgb(0, 0, 0);")
        self.TestCaseTable.setStyleSheet("background-color: rgb(255, 255, 255);")

        # CheckBox to sellect all testCase
        self.checkboxSellectAll = QCheckBox()
        self.checkboxSellectAll.setChecked(True)
        checkbox_item = QWidget()
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkboxSellectAll)
        checkbox_layout.setAlignment(Qt.AlignCenter)  # Align the checkbox to the center
        checkbox_item.setLayout(checkbox_layout)
        self.TestCaseTable.setCellWidget(0, 0, checkbox_item)
        self.checkboxSellectAll.stateChanged.connect(self.onSellectAllCheckBoxClicked)

        testCaseAll = QTableWidgetItem(f"All Test Cases")
        testCaseAll.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(0, 1, testCaseAll)
        self.TestCaseTable.setItem(0, 2, QTableWidgetItem(f"     [Verify]: All test cases"))

        self.loadTCToTable()


    def onSellectAllCheckBoxClicked(self):
        isChecked = False
        if (self.checkboxSellectAll.isChecked() == True):
            isChecked = True
        for checkbox in self.mCheckBoxList.values():
            checkbox.setChecked(isChecked)


    def setupRobotTestCaseTable(self, totalRow = 0):
        self.currentRow = 1
        self.TestCaseTable.clear()
        self.TestCaseTable.setColumnCount(5)
        self.TestCaseTable.setRowCount(totalRow + 1)
        self.TestCaseTable.setHorizontalHeaderLabels(["Select", "File", "Test Case", "Test Step", "Test Result"])

        header = self.TestCaseTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: lightblue; font-size: 12pt; }")
        vheader = self.TestCaseTable.verticalHeader()
        vheader.setStyleSheet("QHeaderView::section { font-size: 12pt; }")
        self.TestCaseTable.verticalHeader().setVisible(False)

        self.TestCaseTable.setColumnWidth(0, 70)
        self.TestCaseTable.setColumnWidth(1, 200)
        self.TestCaseTable.setColumnWidth(2, 600)
        self.TestCaseTable.setColumnWidth(3, 800)
        self.TestCaseTable.setColumnWidth(4, 160)
        self.TestCaseTable.setStyleSheet("gridline-color: rgb(0, 0, 0);")
        self.TestCaseTable.setStyleSheet("background-color: rgb(255, 255, 255);")

        # CheckBox to sellect all testCase
        self.checkboxSellectAll = QCheckBox()
        self.checkboxSellectAll.setChecked(False)
        checkbox_item = QWidget()
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkboxSellectAll)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_item.setLayout(checkbox_layout)
        self.TestCaseTable.setCellWidget(0, 0, checkbox_item)
        self.checkboxSellectAll.stateChanged.connect(self.selectAllRobotTC)

        testCaseAll = QTableWidgetItem(f"All Test Cases")
        testCaseAll.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(0, 1, testCaseAll)
        self.TestCaseTable.setItem(0, 2, QTableWidgetItem(f"[Verify]: All test cases"))

    def selectAllRobotTC(self):
        isChecked = self.checkboxSellectAll.isChecked()
        for row in range(1, self.TestCaseTable.rowCount()):
            checkboxWidget = self.TestCaseTable.cellWidget(row, 0)
            if checkboxWidget:
                checkbox = checkboxWidget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(isChecked)


    def checkboxStateChanged(self, state):
        sender = self.sender()
        if isinstance(sender, QCheckBox):
            for key, checkbox in self.mCheckBoxList.items():
                if checkbox is sender:
                    _isChecked = sender.isChecked()
                    self.mTaskManager.enableTestCase(key, _isChecked)
                    if (_isChecked == True):
                        self.TestCaseEnabled += 1
                    else:
                        self.TestCaseEnabled -= 1
        self.updateTestCaseAmount()

    def TCcheckBoxStateChanged(self, state):
        sender = self.sender()
        if sender:
            for row, checkbox in self.TCcheckBoxList.items():
                if checkbox is sender:
                    isChecked = sender.isChecked()
                    if isChecked and self.TestCaseTable.item(row, 1) is None:
                        self.TestCaseEnabled += 1
                    elif isChecked == False and self.TestCaseTable.item(row, 1) is None:
                        self.TestCaseEnabled -= 1
                    break
                
        self.updateRobotTestCaseAmount()


    def isCheckBoxChecked(self, row, column):
        cell_widget = self.TestCaseTable.cellWidget(row, column)
        if cell_widget and isinstance(cell_widget, QCheckBox):
            return cell_widget.isChecked()
        return False

# Set/Get Device status
    def setDeviceState(self, state):
        if self.mdeviceStatus != state:
            self.mdeviceStatus = state
            self.deviceStatus.setText(state)
            if self.mdeviceStatus == NORMAL:
                if (self.AutoKeepAliveButton.isChecked() == True):
                    self.keepBoardAlive()

                if (self.AutoForwardLogButton.isChecked()):
                    self.slddCmd.forwardLog()

                self.deviceStatus.setStyleSheet("background-color: rgb(180, 255, 186);\n"
                                            "border-color: rgb(115, 172, 172);")
                self.Console.append("Booting completed !\n")

            elif self.mdeviceStatus == DISCONNECTED:
                self.deviceStatus.setStyleSheet("background-color: rgb(253, 255, 152);\n"
                                            "border-color: rgb(253, 255, 152);")
                self.Console.append("Board is disconnected !\n")

            elif self.mdeviceStatus == BOOTING:
                self.displayBoardInformation()
                self.deviceStatus.setStyleSheet("background-color: rgb(151, 226, 226);\n"
                                            "border-color: rgb(115, 172, 172);")
                self.Console.append("Board is booting ...\n")

                self.boardName = "_".join(self.SWversionDisplayer.text().split("_")[:2])
                if self.boardName == "JLR_VCM":
                    self.defaultDownloadURL = f'{VCM_ARTIFACTORY_BASE_URL}/VCM_DAILY_BUILD_{datetime.now().strftime("%y%m%d")}/debug/upload_images.tar.gz'
                    self.downloadImgURL.setText(self.defaultDownloadURL)
                elif self.boardName == "JLR_TCUA":
                    self.defaultDownloadURL = f'{TCUA_ARTIFACTORY_BASE_URL}/TCUA_DAILY_BUILD_{datetime.now().strftime("%y%m%d")}/debug/upload_images.tar.gz'
                    self.downloadImgURL.setText(self.defaultDownloadURL)
            print(f"current device Status: [{self.mdeviceStatus}]")

    def getDeviceState(self):
        return self.mdeviceStatus

# Set Test result
    def setTestResult(self, testCaseId, result):
        itemTcName = QTableWidgetItem(result)
        itemTcName.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(testCaseId, 4, itemTcName)
        if (result == FAILED or result == "FAIL"):
            itemTcName.setBackground(QColor(255, 111, 111))     # Red background color
        elif (result == PASSED or result == "PASS"):
            itemTcName.setBackground(QColor(94, 189, 140))      # Green background color
        elif (result == "SKIP"):
            itemTcName.setBackground(QColor(255, 255, 0))       # Yellow background color


    def updateExecutedTime(self, testCaseId):
        position = LIST_TC_POSITION[testCaseId]
        end_time = time.time()
        elapsed_time = end_time - self.startedTestTime
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = "{:0>2}:{:0>2}:{:0>2}".format(int(hours), int(minutes), int(seconds))
        itemTcName = QTableWidgetItem(f"{time_str}")
        itemTcName.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(position, 5, itemTcName)
# Handle messages
    def handleMessage(self, message):
        print("OK")

# Handle WatchDog
    def onTimerWatchDogTimerTimeout(self):
        self.watchDogTimer.stop()
        self.onHandlePowerReset()


# Handle Power Source event
    def turnOffVBAT(self):
        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(VBAT_OFF)
        else:
            self.show_alert("Failed to connect", "COM ports are not available")

    def enableBUB(self):
        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(BUB_ON)
        else:
            self.show_alert("Failed to connect", "COM ports are not available")

# Clear Test Result:
    def clearTestResult(self):
        num_columns = self.TestCaseTable.rowCount()
        for tc in range(0, num_columns):
            itemTcName = QTableWidgetItem(f"")
            itemTcName.setTextAlignment(Qt.AlignCenter)
            self.TestCaseTable.setItem(tc, 4, itemTcName)
            itemTcName.setBackground(QColor(255, 255, 255))  # Default background color
            executedTime = QTableWidgetItem(f"")
            itemTcName.setTextAlignment(Qt.AlignCenter)
            self.TestCaseTable.setItem(tc, 5, executedTime)
            executedTime.setBackground(QColor(255, 255, 255))  # Default background color

        if (self.TestCaseEnabled == 0):
            self.progressBar.setProperty("value", 0)
        else: self.progressBar.setProperty("value", (self.countTestResult/self.TestCaseEnabled)*100)
        totalExecutedTimeItem = QTableWidgetItem(f"")
        totalExecutedTimeItem.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(0, 5, totalExecutedTimeItem)

# Update total test case numer
    def updateTestCaseAmount(self):
        self.TestResultDisplayer.setText(f"{self.countTestResult}/{self.TestCaseEnabled}")
        if (self.TestCaseEnabled == 0):
            self.progressBar.setProperty("value", 0)
        else: self.progressBar.setProperty("value", (self.countTestResult/self.TestCaseEnabled)*100)

    def updateRobotTestCaseAmount(self, countRobotTestResult=0):
        self.TestResultDisplayer.setText(f"{countRobotTestResult}/{self.TestCaseEnabled}")
        if (self.TestCaseEnabled == 0):
            self.progressBar.setProperty("value", 0)
        else: self.progressBar.setProperty("value", (countRobotTestResult/self.TestCaseEnabled)*100)

    def updateTotalExecutedTime(self):
        end_time = time.time()
        totalExecutedTime = end_time - self.executedTime
        hours, remainder = divmod(totalExecutedTime, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = "{:0>2}:{:0>2}:{:0>2}".format(int(hours), int(minutes), int(seconds))
        totalExecutedTimeItem = QTableWidgetItem(f"{time_str}")
        totalExecutedTimeItem.setTextAlignment(Qt.AlignCenter)
        self.TestCaseTable.setItem(0, 5, totalExecutedTimeItem)


    def initSlddList(self):
        print("init SlddList")
        self.data = load_data_from_json('sldd.json')
        self.Module = [_module["name"] for _module in self.data["Module"]]
        self.ModuleList.addItems(self.Module)
        selected_Module = self.ModuleList.currentText()
        slddCommand = [sldd for _module in self.data["Module"] if _module["name"] == selected_Module for sldd in _module["sldd"]]
        self.slddList.clear()
        self.slddList.addItems(slddCommand)
        self.ModuleList.currentIndexChanged.connect(self.onModuleSellected)


    def onModuleSellected(self):
        print("onModuleSellected")
        selected_Module = self.ModuleList.currentText()
        slddCommand = [sldd for _module in self.data["Module"] if _module["name"] == selected_Module for sldd in _module["sldd"]]
        self.slddList.clear()
        self.slddList.addItems(slddCommand)


    def exportTestResult(self):
        df = pd.DataFrame(index=range(self.TestCaseTable.rowCount()), columns=range(self.TestCaseTable.columnCount()))

        for row in range(self.TestCaseTable.rowCount()):
            for column in range(self.TestCaseTable.columnCount()):
                item = self.TestCaseTable.item(row, column)
                if item is not None:
                    df.at[row, column] = item.text()
        file_name = QFileDialog()
        file_name, _ = QFileDialog.getSaveFileName(file_name, "Save File", "", "Excel Files (*.xlsx)")
        if file_name:
            wb = Workbook()
            ws = wb.active

            for r in dataframe_to_rows(df, index=False, header=False):
                ws.append(r)

            wb.save(file_name)

    def keepBoardAlive(self):
        self.slddCmd.keepAlive()

    def findHardwareVersion(self, input_str):
        key_value = re.search(r'\ lge.hw_revision\s*=\s*([^\s]+)', input_str)
        if key_value:
            return key_value.group(1)
        else:
            return "Not Found"

# Config for VCM Project
    def displayAvailableVCMBoard(self):
        slddCmd = slddCommand()

        # Print information about the connected devices
        tmpList = slddCmd.getListDeviceID()
        listDeviceID = []
        for id in tmpList:
            if id in VCM_DEVICE_ID:
                id = VCM_DEVICE_ID[id]
            listDeviceID.append(id)

        if self.VCMListDevice != listDeviceID:
            self.VCMListDevice = listDeviceID
            self.VCMTestingBoardBox.clear()
            self.SendingTC10BoardBox.clear()
            self.VCMTestingBoardBox.addItems(self.VCMListDevice)
            self.SendingTC10BoardBox.addItems(self.VCMListDevice)

    def onClickTestingBoardConnectButton(self):
        if self.VCMTestingBoardBox.currentText() != "":
            boardID = self.VCMTestingBoardBox.currentText()
            if boardID in VCM_BOARD:
                boardID = VCM_BOARD[boardID]
            self.VCMTestingBoardID = boardID
            print(self.VCMTestingBoardID)
            self.mTaskManager.setDeivceID(self.VCMTestingBoardID)
            self.mdeviceMonitor.setDeviceID(self.VCMTestingBoardID)
        print(f"onClickTestingBoardConnectButton : {self.VCMTestingBoardID}")

    def onClickSendingTC10BoardConnectButton(self):
        if self.SendingTC10BoardBox.currentText() != "":
            boardID = self.SendingTC10BoardBox.currentText()
            if boardID in VCM_BOARD:
                boardID = VCM_BOARD[boardID]
            self.VCMSendingTC10BoardID = boardID
            print(self.VCMSendingTC10BoardID)
            self.mEthernetManager.setDeviceID(self.VCMSendingTC10BoardID)
        print(f"onClickSendingTC10BoardConnectButton : {self.VCMSendingTC10BoardID}")

    def onClickTC10OnButton(self):
        print(self.VCMSendingTC10BoardID)
        if UNKNOWN_ID != self.VCMSendingTC10BoardID:
            self.mEthernetManager.sendTC10On()
        else:
            print("DEVICE IS NOT FOUND --> CANNOT SENDING TC10 ON")

    def onClickTC10OffButton(self):
        print(self.VCMSendingTC10BoardID)
        if UNKNOWN_ID != self.VCMSendingTC10BoardID:
            self.mEthernetManager.sendTC10Off()
        else:
            print("DEVICE IS NOT FOUND --> CANNOT SENDING TC10 OFF")

# Load TestCase Information to Table
    def open_file_dialog(self):
        try:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            if self.testFileType == "json":
                file_dialog.setNameFilter("Text files (*.json);;All files (*.*)")
            elif self.testFileType == "robot":
                file_dialog.setNameFilter("Text files (*.robot);;All files (*.*)")
                if self.boardName == "JLR_VCM":
                    self.robotFilePath = "../testsuites_vcm"
                elif self.boardName == "JLR_TCUA":
                    self.robotFilePath = "../testsuites_tcua"
                self.robotFilePath = os.path.abspath(self.robotFilePath)
                if os.path.isdir(self.robotFilePath):
                    file_dialog.setDirectory(self.robotFilePath)
                else:
                    self.show_alert("Directory Not Found", f"Directory does not exist: {self.robotFilePath}")
                    return None

            if file_dialog.exec_():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    if self.testFileType == "json":
                        selected_file = selected_files[0]
                        if selected_file:
                            print(f"Selected file: {selected_file}")
                            return selected_file
                        else:
                            self.show_alert("Error", "Invalid file path selected.")
                    elif self.testFileType == "robot":
                        return selected_files   
                else:
                    self.show_alert("Error", "No file selected.")
        except FileNotFoundError:
            print("File not found. Please check the file path.")

    def loadConfigTestCase(self):
        self.testFileType = "json"
        path = self.open_file_dialog()
        if (path == None):
            self.show_alert("Failed to load Configuration", "please select file config")
        else:
            totalTC = self.loadJSONTestCases(path)
            self.setupTestCaseTable(totalTC)
            self.mTaskManager.setNumberTC(self.totalTC+1)
    
    def loadRobotTestCase(self):
        self.TestCaseEnabled = 0
        self.TestResultDisplayer.setText(f"{self.countTestResult}/{self.TestCaseEnabled}")
        self.testFileType = "robot"
        path = self.open_file_dialog()
        if (path == None):
            self.show_alert("Failed to load Robot", "Please select robot file")
        else:
            self.TCcheckBoxList = {}
            self.setupRobotTestCaseTable()
            for file_path in path:
                self.loadRobotFile(file_path)

            checkBox = QCheckBox()
            checkBox.setChecked(True)
            self.TCcheckBoxList = self.mLoadRobotTestCase.TCcheckBoxList
            for checkBox in self.TCcheckBoxList.values():
                checkBox.stateChanged.connect(self.TCcheckBoxStateChanged)

    def loadJSONTestCases(self, JsonName):
        self.TestCaseData = load_data_from_json(JsonName)
        id = 0
        totalRow = 0
        for test_case in self.TestCaseData[MODULE]:
            id+=1
            LIST_TC_NAME.update({id: test_case[TC_NAME]})

            testStep = []
            for step in test_case[TC_TEST_STEP]:
                testStep.append(step)
            LIST_TEST_STEP.update({id: testStep})

            description=[]
            for desc in test_case[TC_DESCRIPTON]:
                description.append(desc)
            LIST_TEST_DESCRIPTION.update({id: description})

            expectedResult=[]
            for expt in test_case[TC_EXPECTED_RESULT]:
                totalRow+=1
                expectedResult.append(expt)
            LIST_EXPECTED_RESULT.update({id: expectedResult})

        self.totalTC = self.mtestDatabase.getTestCaseCounter(LIST_TC_NAME)
        self.TestCaseEnabled = self.mtestDatabase.getTestCaseCounter(LIST_TC_NAME)
        self.TestResultDisplayer.setText(f"0/{self.totalTC}")
        return totalRow

    def loadTCToTable(self):
        self.mCheckBoxList = {}
        print(LIST_TC_NAME)
        currentIndex = 1
        for testCase in range(TEST_CASE_START , self.totalTC+1):
            checkBoxPosition = currentIndex
            LIST_TC_POSITION.update({testCase: checkBoxPosition})
            tcname = self.mtestDatabase.getTCName(testCase, LIST_TC_NAME)
            itemTcName = QTableWidgetItem(f"{tcname}")
            itemTcName.setTextAlignment(Qt.AlignCenter)
            self.TestCaseTable.setItem(currentIndex, 1, itemTcName)
            for id in range(0, len(LIST_TEST_DESCRIPTION[testCase])):
                descrip = self.mtestDatabase.getTestCaseDescription(testCase, LIST_TEST_DESCRIPTION)
                self.TestCaseTable.setItem(currentIndex, 2, QTableWidgetItem(f"     {descrip[id]}"))
                expectRes = self.mtestDatabase.getTestCaseExpectedResult(testCase, LIST_EXPECTED_RESULT)
                self.TestCaseTable.setItem(currentIndex, 3, QTableWidgetItem(f"     {expectRes[id]}"))
                currentIndex+=1
                print(f"{tcname} -- {descrip} -- {expectRes}")

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.mCheckBoxList[testCase] = checkbox
            checkbox_item = QWidget()
            checkbox_layout = QVBoxLayout()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)  # Align the checkbox to the center
            checkbox_item.setLayout(checkbox_layout)
            self.TestCaseTable.setCellWidget(checkBoxPosition, 0, checkbox_item)

        for checkbox in self.mCheckBoxList.values():
            checkbox.stateChanged.connect(self.checkboxStateChanged)

    def isFileExisted(self, fileName):
        # Check if the file exists in the current working directory
        if os.path.exists(fileName): return True
        else: return False

    def loadDefaultTestConfiguration(self):
        if (self.isFileExisted("TCUA_Power_TC.json")):
            totalTC = self.loadJSONTestCases("TCUA_Power_TC.json")
            self.setupTestCaseTable(totalTC)
            self.mTaskManager.setNumberTC(self.totalTC+1)

    def loadRobotFile(self, robotFilePath):
        if robotFilePath:
            self.processRobotFile(robotFilePath)
        else:
            self.show_alert("Error", "No valid file path to process.")


    def processRobotFile(self, filePath):
        model = get_model(filePath)
        self.mLoadRobotTestCase = LoadRobotTestCase(self.TestCaseTable, self.currentRow, self.TCcheckBoxList)
        self.mLoadRobotTestCase.visit(model)
        self.currentRow = self.mLoadRobotTestCase.currentRow


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    TestingTool = QtWidgets.QMainWindow()
    mainApp = UI_Power_tool(TestingTool)
    mainApp.TestingTool.show()
    sys.exit(app.exec_())
