import os
import re
import shutil
import tarfile
import subprocess
from commonVariable import *
import serial.tools.list_ports
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
        self.programmerPath = ''
        self.searchPath = ''
        self.rawProgramXml = RAWPROGRAM_PATH
        self.patchXml = PATCH_PATH
        self.qfilExePath = QFIL_EXE_PATH

    def getQualcommPort(self):
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
                self.flashSignal.emit(f"Extraction successful. Files extracted to: {extractPath}")
                return True
            
        except PermissionError:
            self.flashSignal.emit(f"Error: Permission denied for extraction path: {extractPath}")
        except Exception as e:
            self.flashSignal.emit(f"Error during extraction: {e}")
        return False

    def flashImage(self):
        if self.boardName == "JLR_VCM":
            self.searchPath = os.path.join(self.boardDir, VCM_DEBUG_PATH)
            self.programmerPath = os.path.join(self.searchPath, VCM_PROGRAMMER_PATH)
        elif self.boardName == "JLR_TCUA":
            self.searchPath = os.path.join(self.boardDir, TCUA_DEBUG_PATH)
            self.programmerPath = os.path.join(self.searchPath, TCUA_PROGRAMMER_PATH)
        else:
            raise ValueError(f"No valid board name: {self.boardName}")

        cmd = (
            f'{self.qfilExePath}\
            -DOWNLOADFLAT\
            -MODE=3\
            -COM={self.flashPort}\
            -FLATBUILDPATH="C:"\
            -METABUILD=";"\
            -FLATBUILDFORCEOVERRIDE=True\
            -SEARCHPATH="{self.searchPath}"\
            -PBLDOWNLOADPROTOCOL=0\
            -PROGRAMMER=True;"{self.programmerPath}"\
            -RAWPROGRAM="{self.rawProgramXml}"\
            -PATCH="{self.patchXml}"\
            -ACKRAWDATAEVERYNUMPACKETS=False;100\
            -MAXPAYLOADSIZETOTARGETINBYTES=False;49152\
            -RESETAFTERDOWNLOAD=True\
            -ERASEALL=True\
            -QCNAUTOBACKUPRESTORE:True\
            -DEVICETYPE="nand"\
            -PLATFORM="8x26"'
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

    def handeFlashImage(self):
        try:
            if not self.getQualcommPort():
                return False

            if not self.extractImageFile():
                return False
            
            if not self.flashImage():
                return False
            
            return True
        
        except Exception as e:
            self.flashSignal.emit(f"Error during flashing: {e}")
            return False

    def stop(self):
        if self.isFlashing:
            self.flashProcess.terminate()
            self.isFlashing = False
            self.flashSignal.emit("Flash stopped")