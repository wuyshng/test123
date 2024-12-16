import os
import re
import requests
from datetime import datetime, timedelta
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject

class DownloadManager(QObject):
    downloadSignal = pyqtSignal(str)
    downloadProgressSignal = pyqtSignal(int)
    defaultImgURLSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.isDownloading = False
        self.isStopped = False
        self.boardName = None
        self.boardInfo = None
        self.imageName = "upload_images.tar.gz"
        self.dailyRepo = None
        self.downloadFromURL = ""

    def getBoardInfo(self):
        if self.boardName == "JLR_VCM":
            self.boardInfo = {
                "ARTIFACTORY_BASE_URL": "http://vbas.lge.com:8082/artifactory/vcm/DAILY",
                "SITE_USERNAME": "vcm_dev",
                "SITE_PASSWORD": "JLRvcm!1234",
                "BOARD_NAME": "VCM"
            }
        elif self.boardName == "JLR_TCUA":
            self.boardInfo = {
                "ARTIFACTORY_BASE_URL": "http://vbas.lge.com:8082/artifactory/tcua/DAILY",
                "SITE_USERNAME": None,
                "SITE_PASSWORD": None,
                "BOARD_NAME": "TCUA"
            }
        else:
            raise ValueError(f"No valid board name: {self.boardName}")
        return self.boardInfo

    def createImgDirectory(self):
        baseDir = os.path.join(os.path.dirname(os.getcwd()), "images")
        boardDir = os.path.join(baseDir, self.boardName)
        os.makedirs(boardDir, exist_ok=True)
        return boardDir

    def downloadImgFile(self, url, dest_dir, username=None, password=None):
        try:
            with requests.get(url, auth=(username, password) if username and password else None, stream=True) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("Content-Length", 0))
                filename = os.path.join(dest_dir, url.split("/")[-1])
                self.downloadSignal.emit(
                                        f"Image Name: {self.imageName}\n"
                                        f"Daily Repo: {self.dailyRepo}\n"
                                        f"Download from {url}\n"
                                        f"Downloading image ..."
                )
                self.isDownloading = True
                downloaded_size = 0
                with open(filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.isStopped:
                            self.downloadSignal("Download stopped.\n")
                            return False
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)

                            self.progress_percentage = int((downloaded_size / total_size) * 100)
                            self.downloadProgressSignal.emit(self.progress_percentage)

                self.downloadSignal.emit(f"Download successful. File saved at: {dest_dir}\n")
                self.isDownloading = False
                return True

        except requests.RequestException as e:
            self.downloadSignal.emit(f"Error:{e} ")
            return False

    def findValidImg(self, baseURL, dateStr, dest_dir, username=None, password=None):
        self.downloadSignal.emit("Finding the valid image ...")
        current_date = datetime.strptime(dateStr, "%y%m%d")

        while True:
            try_date = (current_date - timedelta(days=0)).strftime("%y%m%d")
            self.dailyRepo = f"{self.boardInfo['BOARD_NAME']}_DAILY_BUILD_{try_date}"
            try_url = f"{baseURL}/{self.dailyRepo}/debug/{self.imageName}"

            if self.isStopped == True:
                return False

            if self.downloadImgFile(try_url, dest_dir, username, password):
                return True
            current_date -= timedelta(days=1)

    def handleDownloadImg(self):
        try:
            boardInfo = self.getBoardInfo()
            artifactoryBaseURL = boardInfo["ARTIFACTORY_BASE_URL"]
            username = boardInfo["SITE_USERNAME"]
            password = boardInfo["SITE_PASSWORD"]

            currentDate = datetime.now().strftime("%y%m%d")
            self.dailyRepo = f"{boardInfo['BOARD_NAME']}_DAILY_BUILD_{currentDate}"
            self.defaultImgURLSignal.emit(f'{boardInfo["ARTIFACTORY_BASE_URL"]}/{self.dailyRepo}/debug/{self.imageName}')

            self.boardDir = self.createImgDirectory()

            if self.downloadFromURL != "":
                match = re.search(f"{boardInfo['BOARD_NAME']}_DAILY_BUILD_(\\d+)", self.downloadFromURL)
                if match:
                    self.dailyRepo = f"{boardInfo['BOARD_NAME']}_DAILY_BUILD_{match.group(1)}"

                if not self.downloadImgFile(self.downloadFromURL, self.boardDir, username, password):
                    # self.downloadSignal.emit("Download stopped.\n")
                    return False
                else:
                    return True

            else:
                if not self.findValidImg(artifactoryBaseURL, currentDate, self.boardDir, username, password):
                    self.downloadSignal.emit("Download stopped.\n")
                    return False
                else:
                    return True

        except Exception as e:
            # self.downloadSignal.emit(f"Error during execution: {e}")
            print(f"Error during execution: {e}")

    def stop(self):
        if self.isDownloading == True:
            self.isStopped = True
