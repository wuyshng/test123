import os
import re
import shutil
import tarfile
import subprocess
import serial.tools.list_ports
from PyQt5.QtCore import pyqtSignal, QObject

class FlashManager(QObject):
    flashSignal = pyqtSignal(str)
    flashProgressSignal = pyqtSignal(int)

    def __init__(self, boardName, boardDir):
        super().__init__()
        self.boardName = boardName
        self.boardDir = boardDir
        self.portNum = -1
        self.programmerPath = ''
        self.searchPath = ''
        self.rawProgramXml = "rawprogram_nand_p4K_b256K.xml"
        self.patchXml = "patch_p4K_b256K.xml"
        self.qfilExePath = r"C:\Program Files (x86)\Qualcomm\QPST\bin\QFIL.exe"

    def getQualcommPort(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Qualcomm HS-USB QDLoader 9008" in port.description:
                return port.device
        return -1

    def extractImgFile(self):
        self.extractPath = self.boardDir
        self.flashSignal.emit(f"{self.extractPath}")
        try:
            upload_images_folder = os.path.join(self.extractPath, 'upload_images')
            if os.path.exists(upload_images_folder):
                self.flashSignal.emit(f"Removing previous extracted folder: {upload_images_folder}")
                shutil.rmtree(upload_images_folder)

            if not os.path.exists(self.extractPath):
                os.makedirs(self.extractPath)
            self.flashSignal.emit(f"Extracting upload_images.tar.gz ...")

            imageFilePath = os.path.join(self.boardDir, "upload_images.tar.gz")
            if not os.path.isfile(imageFilePath):
                self.flashSignal.emit(f"Error: The image file {imageFilePath} does not exist.")
                return

            with tarfile.open(imageFilePath, "r:gz") as tar:
                tar.extractall(path=self.extractPath)
                self.flashSignal.emit(f"Extraction successful. Files extracted to: {self.extractPath}")
        except PermissionError:
            self.flashSignal.emit(f"Error: Permission denied for extraction path: {self.extractPath}")
        except Exception as e:
            self.flashSignal.emit(f"Error during extraction: {e}")

    def flashImg(self):
        if self.boardName == "JLR_VCM":
            self.searchPath = os.path.join(self.extractPath, r"upload_images\nad\vcm-sa515m-debug")
            self.programmerPath = os.path.join(self.searchPath, "prog_firehose_sdx55.mbn")
        elif self.boardName == "JLR_TCUA":
            self.searchPath = os.path.join(self.extractPath, r"upload_images\nad\jlr_tcua-mdm9607-debug_4k")
            self.programmerPath = os.path.join(self.searchPath, "prog_nand_firehose_9x07.mbn")
        else:
            raise ValueError(f"No valid board name: {self.boardName}")

        cmd = (
            f'{self.qfilExePath}\
            -DOWNLOADFLAT\
            -MODE=3\
            -COM={self.portNum}\
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
            -METABUILD=";"\
            -FLATBUILDPATH="C:"\
            -FLATBUILDFORCEOVERRIDE=True\
            -QCNAUTOBACKUPRESTORE:True\
            -ERASEALL=True'
        )
        self.flashProgressSignal.emit(0)
        self.flashSignal.emit("Flashing image ...")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )

            for line in iter(process.stdout.readline, ""):
                line = line.strip()
                if "percent files transferred" in line:
                    match = re.search(r"(\d+)\.\d+%", line)
                    if match:
                        percentage = int(match.group(1))
                        self.flashProgressSignal.emit(percentage)

            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                self.flashSignal.emit("Flash successful!")
            else:
                self.flashSignal.emit(f"Flash failed with exit code: {process.returncode}")
        except subprocess.CalledProcessError as e:
            self.flashSignal.emit(f"Flashing failed: {e}")
        except Exception as e:
            self.flashSignal.emit(f"An unexpected error occurred: {e}")

    def handleFlashImg(self):
        self.portNum = self.getQualcommPort()
        if self.portNum == -1:
            self.flashSignal.emit("No valid Qualcomm port detected. Flash process aborted.")
            return

        self.extractImgFile()
        self.flashImg()
