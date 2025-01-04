import os
import re
import requests
from commonVariable import *
from datetime import datetime, timedelta
from PyQt5.QtCore import pyqtSignal, QObject

class DownloadManager(QObject):
    downloadSignal = pyqtSignal(str)
    downloadProgressSignal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.isDownloading = False
        self.isStopped = False
        self.boardName = None
        self.boardInfo = None
        self.dailyRepo = None
        self.imageFile = IMAGE_FILE
        self.downloadFromURL = NO_IMAGE_URL

    def getBoardInfo(self):
        if self.boardName == JLR_VCM:
            self.boardInfo = {
                "ARTIFACTORY_BASE_URL": VCM_ARTIFACTORY_BASE_URL,
                "SITE_USERNAME": VCM_SITE_USERNAME,
                "SITE_PASSWORD": VCM_SITE_PASSWORD,
                "BOARD_NAME": VCM
            }
        elif self.boardName == JLR_TCUA:
            self.boardInfo = {
                "ARTIFACTORY_BASE_URL": TCUA_ARTIFACTORY_BASE_URL,
                "SITE_USERNAME": TCUA_SITE_USERNAME,
                "SITE_PASSWORD": TCUA_SITE_PASSWORD,
                "BOARD_NAME": TCUA
            }
        else:
            raise ValueError(f"No valid board name: {self.boardName}")
        return self.boardInfo

    def createImageDirectory(self):
        boardDir = os.path.join(os.path.dirname(os.getcwd()), "images", self.boardName)
        os.makedirs(boardDir, exist_ok=True)
        return boardDir

    def downloadImageFile(self, url, destDir, username=None, password=None):
        try:
            match = re.search(r'/DAILY/([^/]+)/', url)
            if match:
                dailyRepo = match.group(1)
                
            with requests.get(url, auth=(username, password) if username and password else None, stream=True) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("Content-Length", 0))
                filename = os.path.join(destDir, url.split("/")[-1])
                self.downloadSignal.emit(
                                        f"Image File: {self.imageFile}\n"
                                        f"Daily Repository: {dailyRepo}\n"
                                        f"Download from {url}\n"
                                        f"Downloading image ..."
                )
                self.isDownloading = True
                downloaded_size = 0
                with open(filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=65536):
                        if self.isStopped:
                            self.downloadSignal.emit("Download stopped.\n")
                            return False
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)

                            progress_percentage = int((downloaded_size / total_size) * 100)
                            self.downloadProgressSignal.emit(progress_percentage)

                self.downloadSignal.emit(f"Download successful. File saved at: {destDir}\n")
                self.isDownloading = False
                return True

        except requests.RequestException as e:
            self.downloadSignal.emit(f"Download failed: {e}")
            return False

    def findValidImage(self, baseURL, dateStr, destDir, username=None, password=None):
        self.downloadSignal.emit("Finding the valid image ...")
        currentDate = datetime.strptime(dateStr, "%y%m%d")

        while not self.isStopped:
            tryDate = currentDate.strftime("%y%m%d")
            self.dailyRepo = tryDate
            tryURL = f"{baseURL}{self.dailyRepo}/debug/{self.imageFile}"

            if self.downloadImageFile(tryURL, destDir, username, password):
                return True

            currentDate -= timedelta(days=1)

        self.downloadSignal.emit("Download stopped.\n")
        return False

    def handleDownloadImage(self):
        try:
            boardInfo = self.getBoardInfo()
            artifactoryBaseURL = boardInfo["ARTIFACTORY_BASE_URL"]
            username = boardInfo["SITE_USERNAME"]
            password = boardInfo["SITE_PASSWORD"]

            currentDate = datetime.now().strftime("%y%m%d")
            self.dailyRepo = currentDate

            self.boardDir = self.createImageDirectory()

            if self.downloadFromURL != NO_IMAGE_URL:
                match = re.search(f"{boardInfo['ARTIFACTORY_BASE_URL']}(\\d+)", self.downloadFromURL)
                if match:
                    self.dailyRepo = match.group(1)

                return self.downloadImageFile(self.downloadFromURL, self.boardDir, username, password)
            
            return self.findValidImage(artifactoryBaseURL, currentDate, self.boardDir, username, password)

        except Exception as e:
            print(f"Error during execution: {e}")
            return False

    def stop(self):
        if self.isDownloading:
            self.isStopped = True
