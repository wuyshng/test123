import os
import re
import shutil
import tarfile
import subprocess
from time import sleep
from commonVariable import *
import serial.tools.list_ports
from sendSLDDCommand import slddCommand
from ArduinoManager import ArduinoManager
from PyQt5.QtCore import pyqtSignal, QObject

class FlashManager(QObject):
    flashSignal = pyqtSignal(str)
    flashProgressSignal = pyqtSignal(int)

    def __init__(self, boardName, boardDir):
        super().__init__()
        self.isFlashing = False
        self.flashProcess = None
        self.boardName = boardName
        self.boardDir = boardDir
        self.flashPort = -1
        self.programmerPath = ""
        self.searchPath = ""
        self.rawProgramXml = RAWPROGRAM_PATH
        self.patchXml = PATCH_PATH
        self.qfilExePath = QFIL_EXE_PATH
        self.vcmDevice = UNKNOWN_ID
        self.imageVersion = NO_IMAGE_VERSION
        self.ArduinoPort = NO_PORT_CONNECTED

    def getQualcommPort(self):
        sleep(20)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Qualcomm HS-USB QDLoader 9008" in port.description:
                match = re.search(r'\d+', port.device)
                if match:
                    self.flashPort = int(match.group())
                    return True

        self.flashSignal.emit("Flashing failed: No valid Qualcomm port detected. Please try flashing again.\n")
        return False

    def extractImageFile(self):
        self.flashProgressSignal.emit(0)
        extractPath = self.boardDir
        self.flashSignal.emit(f"{extractPath}")
        try:
            uploadImagesFolder = os.path.join(extractPath, 'upload_images')
            if os.path.exists(uploadImagesFolder):
                self.flashSignal.emit(f"Removing previous extracted folder: {uploadImagesFolder}")
                shutil.rmtree(uploadImagesFolder)

            if not os.path.exists(extractPath):
                os.makedirs(extractPath)

            self.flashSignal.emit(f"Extracting upload_images.tar.gz ...")

            imageFilePath = os.path.join(self.boardDir, "upload_images.tar.gz")
            if not os.path.isfile(imageFilePath):
                self.flashSignal.emit(f"Error: The image file {imageFilePath} does not exist.")
                return False

            with tarfile.open(imageFilePath, "r:gz") as tar:
                tar.extractall(path=extractPath)
                self.flashSignal.emit(f"Extraction successful to: {extractPath}\n")
                return True
            
        except PermissionError:
            self.flashSignal.emit(f"Error: Permission denied for extraction path: {extractPath}")
        except Exception as e:
            self.flashSignal.emit(f"Error during extraction: {e}")
        return False

    def flashImage(self):
        if self.boardName == JLR_VCM:
            self.slddCmd = slddCommand()
            if not self.isVCMDeviceConnected():
                return False
        elif self.boardName == JLR_TCUA:
            if not self.flash_tcua(self.imageVersion):
                return False
        else:
            raise ValueError(f"No valid board name: {self.boardName}")
        
        cmd = (
            f'{self.qfilExePath}\
            -COM={self.flashPort}\
            -MODE=3\
            -DOWNLOADFLAT\
            -PBLDOWNLOADPROTOCOL=0\
            -PROGRAMMER=True;"{self.programmerPath}"\
            -SEARCHPATH="{self.searchPath}"\
            -RAWPROGRAM="{self.rawProgramXml}"\
            -PATCH="{self.patchXml}"\
            -ACKRAWDATAEVERYNUMPACKETS=False;100\
            -MAXPAYLOADSIZETOTARGETINBYTES=False;49152\
            -DEVICETYPE="nand"\
            -PLATFORM="8x26"\
            -RESETAFTERDOWNLOAD=True\
            -FLATBUILDPATH="C:"\
            -FLATBUILDFORCEOVERRIDE=True\
            -QCNAUTOBACKUPRESTORE=True\
            -SPCCODE="000000"\
            -ERASEALL=True'
        )

        self.flashSignal.emit("Flashing image ...")
        self.isFlashing = True

        try:
            self.flashProcess = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )

            for line in iter(self.flashProcess.stdout.readline, ""):
                line = line.strip()
                if "percent files transferred" in line:
                    match = re.search(r"(\d+)\.\d+%", line)
                    if match:
                        percentage = int(match.group(1))
                        self.flashProgressSignal.emit(percentage)
                
                elif "Download Succeed" in line:
                    self.flashSignal.emit("Flash successful!\n")
                    return True

            self.flashProcess.stdout.close()
            self.flashProcess.wait()

            if self.flashProcess.returncode == 0:
                print("Flash process completed successfully.")
                return True
            else:
                print(f"Flash failed with exit code: {self.flashProcess.returncode}")
                return False
        except subprocess.CalledProcessError as e:
            self.flashSignal.emit(f"Flashing failed: {e}\n")
        except Exception as e:
            self.flashSignal.emit(f"An unexpected error occurred: {e}")

    def handleFlashImage(self):
        try:
            if not self.extractImageFile():
                return False
            
            self.getArduinoPort()
        
            if self.boardName == JLR_TCUA:
                if not self.turnOnBootMode():
                    return False
            
            if not self.flashImage():
                return False
            
            self.turnOnNormalMode()

            return True
        
        except Exception as e:
            self.flashSignal.emit(f"Error during flashing: {e}")
            return False
        
    def isVCMDeviceConnected(self):
        self.vcmDevice = JLR_VCM_NAD
        if self.vcmDevice == JLR_VCM_V2X:
            if not  self.flash_sa2150p(self.imageVersion):
                return False
        elif self.vcmDevice == JLR_VCM_NAD:
            if not self.flash_sa515m(self.imageVersion):
                return False
        elif self.vcmDevice == UNKNOWN_ID:
            self.flashSignal.emit("VCM device is not connected. Please connect one VCM device in the VCM tab!")
            return False
        return True
    
    def flash_sa2150p(self, version):
        try:
            self.searchPath = os.path.join(self.boardDir, VCM_SA2150P_PATH[version])
            self.programmerPath = os.path.join(self.searchPath, VCM_SA2150P_PROGRAMMER_PATH)
            self.slddCmd.send_adb_shell_command("reboot edl")
            if not self.getQualcommPort():
                return False
            return True

        except Exception as ex:
            self.flashSignal.emit(f'Failed to flash image to SA2150P. Exception: {ex}')
            return False
        
    def flash_sa515m(self, version):
        try:
            self.searchPath = os.path.join(self.boardDir, VCM_SA515M_PATH[version])
            self.programmerPath = os.path.join(self.searchPath, VCM_SA515M_PROGRAMMER_PATH)
            self.slddCmd.send_adb_shell_command("reboot edl")
            if not self.getQualcommPort():
                return False
            return True

        except Exception as ex:
            self.flashSignal.emit(f'Failed to flash image to SA515M. Exception: {ex}')
            return False
        
    def flash_tcua(self, version):
            self.searchPath = os.path.join(self.boardDir, TCUA_PATH[version])
            self.programmerPath = os.path.join(self.searchPath, TCUA_PROGRAMMER_PATH)
            if not self.getQualcommPort():
                return False
            return True
            
    def turnOnNormalMode(self):
        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(TCUA_VBAT_OFF)
            mArduinomgr.sendCommandRequest(VCM_VBAT_OFF)
            mArduinomgr.sendCommandRequest(BUB_OFF)
            mArduinomgr.sendCommandRequest(BOOT_OFF)
            sleep(1)
            if self.boardName == JLR_TCUA:
                mArduinomgr.sendCommandRequest(TCUA_VBAT_ON)
            elif self.boardName == JLR_VCM:
                mArduinomgr.sendCommandRequest(VCM_VBAT_ON)

    def turnOnBootMode(self):
        if self.ArduinoPort != NO_PORT_CONNECTED:
            mArduinomgr = ArduinoManager(self.ArduinoPort)
            mArduinomgr.sendCommandRequest(BOOT_OFF)
            mArduinomgr.sendCommandRequest(TCUA_VBAT_OFF)
            sleep(1)
            mArduinomgr.sendCommandRequest(BOOT_ON)
            sleep(1)
            mArduinomgr.sendCommandRequest(TCUA_VBAT_ON) 
            return True
        else:
            self.signal.emit("Cannot find arduino port")
            return False
        
    def getArduinoPort(self): 
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB-SERIAL CH340" in port.description or "Arduino Uno" in port.description:
                self.ArduinoPort = f"{port.device}"
                break

    def stop(self):
        if self.isFlashing:
            self.flashProcess.terminate()
            self.isFlashing = False
            self.flashSignal.emit("Flash stopped")