import os
import serial
from time import sleep
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from DownloadManager import DownloadManager
from FlashManager import FlashManager
from ArduinoManager import ArduinoManager
from commonVariable import *

class AutomateQFIL(QtCore.QThread):
    signal = pyqtSignal(str)
    progressSignal = pyqtSignal(int)
    defautDownloadURLSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.boardName = None
        self.isRunning = False
        self.runDownloadOnly = False
        self.runFlashOnly = False
        self.ArduinoPort = NO_PORT_CONNECTED
        self.downloadFromURL = NO_IMAGE_URL

    def run(self):
        self.boardDir = os.path.join(os.path.dirname(os.getcwd()), "images", self.boardName)
        self.mDownloadManager = DownloadManager()
        self.mDownloadManager.downloadSignal.connect(self.signal)
        self.mDownloadManager.downloadProgressSignal.connect(self.progressSignal)
        self.mDownloadManager.defaultImgURLSignal.connect(self.defautDownloadURLSignal)
        self.mFlashManager = FlashManager(self.boardName, self.boardDir)
        self.mFlashManager.flashSignal.connect(self.signal)
        self.mFlashManager.flashProgressSignal.connect(self.progressSignal)
        try:
            if self.runDownloadOnly and self.runFlashOnly == False:
                self.handleDownload()
            elif self.runFlashOnly and self.runDownloadOnly == False:
                self.handleFlash()
            elif self.runDownloadOnly and self.runFlashOnly:
                self.handleDownloadAndFlash()

        except Exception as e:
            self.signal.emit(f"Error during AutomateQFIL process: {e}")

    def handleDownload(self):
        self.isRunning = True
        try:
            if self.downloadFromURL != NO_IMAGE_URL:
                self.mDownloadManager.downloadFromURL = self.downloadFromURL

            self.mDownloadManager.boardName = self.boardName
            result = self.mDownloadManager.handleDownloadImg()
            self.isRunning = False
            return result
        
        except Exception as e:
            self.isRunning = False
            self.signal.emit(f"Error during download: {e}")
            return False
    
    def handleFlash(self):
        ports = serial.tools.list_ports.comports()

        for port in ports:
            print(f"Port: {port.device}")
            print(f"Description: {port.description}")
            if "USB-SERIAL CH340" in port.description or "Arduino Uno" in port.description:
                self.ArduinoPort = f"{port.device}"
                print(f"Arduino connected to Port: {self.ArduinoPort}")
                break

        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(BUB_OFF)
            mArduinomgr.sendCommandRequest(VBAT_OFF)
            mArduinomgr.sendCommandRequest(BUB_ON)
            sleep(1)
            mArduinomgr.sendCommandRequest(VBAT_ON) 
            sleep(1)
        else:
            self.signal.emit("Cannot find arduino port")
            return False
        
        self.mFlashManager.getQualcommPort()
        self.isRunning = True
        try:
            result = self.mFlashManager.handleFlashImg()
            self.isRunning = False
            if result == True:
                mArduinomgr.sendCommandRequest(BUB_OFF)
                mArduinomgr.sendCommandRequest(VBAT_OFF)
                mArduinomgr.sendCommandRequest(VBAT_ON)
            return result
        except Exception as e:
            self.isRunning = False
            self.signal.emit(f"Error during flash: {e}")
            return False
    
    def handleDownloadAndFlash(self):
        if not self.handleDownload():
            return
        if not self.handleFlash():
            self.signal.emit("Flash failed.")
        

    def stop(self):
        if self.isRunning == True:
            if self.mDownloadManager.isDownloading == True:
                self.mDownloadManager.stop()
            if self.mFlashManager.isFlashing == True:
                self.mFlashManager.stop()
            self.isRunning = False
            self.exit()
