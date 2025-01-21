import os
from zipfile import ZipFile
from datetime import datetime
from commonVariable import *
from atlassian import Confluence
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class AutomateReportOnCollab:
    def __init__(self):
        self.isError = ""
        self.content = ""
        try:
            self.confluence = Confluence(url=COLLAB_BASE_URL, token=PAT)

            sourceDir = os.path.dirname(os.path.abspath(__file__))
            self.outputDir = os.path.join(sourceDir, "output")
        except Exception as e:
            print(f"Error: {e}")

    def getSanityResultFiles(self, boardName):
        if boardName in FILE_NAMES:
            return FILE_NAMES[boardName]
        else:
            raise ValueError(f"Can not found in files with {boardName}")

    def archiveFiles(self, boardName):
        if not os.path.exists(self.outputDir):
            raise FileNotFoundError(f"The directory {self.outputDir} does not exist.")
        
        files = self.getSanityResultFiles(boardName)
        files_to_archive = []
        for file_type in ['log', 'report']:
            file_path = os.path.join(self.outputDir, files[file_type])
            if os.path.exists(file_path):
                files_to_archive.append(file_path)
            else:
                print(f"Warning: The file {files[file_type]} does not exist in the directory.")
        
        if files_to_archive:
            archive_path = os.path.join(self.outputDir, f"{boardName}.zip")
            with ZipFile(archive_path, 'w') as archive:
                for file in files_to_archive:
                    archive.write(file, os.path.basename(file))
            print(f"Files have been archived to: {archive_path}")
            return archive_path
        else:
            print("No files to archive.")
            return None
        
    def authenticatePage(self):
        try:
            result = self.confluence.page_exists(space=COLLAB_SPACE, title=PARENT_PAGE_TITLE)
            return result
        except Exception as e:
            print(f"Error: {e}")

    def createDailySanityPage(self):
        if not self.authenticatePage():
            print("[Page not found.]")
            return False
        
        parentPageID = self.confluence.get_page_id(space=COLLAB_SPACE, title=PARENT_PAGE_TITLE)
        newPageTitle = self.getNewPageTitle()
        pageBody = self.getPageBody()

        try:
            self.confluence.create_page(space=COLLAB_SPACE, title=newPageTitle, body=pageBody, parent_id=parentPageID)

        except Exception as e:
            print(f"Failed to create page: {e}")

    def getNewPageTitle(self):
        current_date = datetime.now().strftime("%d/%m")
        return f"Daily sanity test {current_date}"
    
    def getPageBody(self):
        self.content += self.updatePageBody
    
    def getTestStatisticsContent(self):
        reportFile = FILE_NAMES[self.boardName]['report'] 
        reportFilePath = os.path.abspath(os.path.join(self.outputDir, reportFile))
        print(f"reportFilePath: {reportFilePath}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"file://{reportFilePath}")
            page.wait_for_selector("#statistics-container")

            content = page.inner_html("#statistics-container")
            browser.close()
            return content
        
    def combineContentWithStyel(self):
        content = self.getTestStatisticsContent()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_file_path = os.path.join(current_dir, STYLE_FILE_NAME)

        if not os.path.exists(style_file_path):
            raise FileNotFoundError(f"Style file not found: {style_file_path}")
        
        with open(style_file_path, "r", encoding="utf-8") as style_file:
            style_content = style_file.read()

        combined_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            {style_content}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """

        return combined_html
    
    def updatePageBody(self):
        if self.isError != "":
            content = f"""
            <h1><strong>{self.boardName}</strong></h1>
            <p>{self.isError}</p>
            """
        else:
            archive_path = self.archiveFiles(self.boardName)
            archive_filename = os.path.basename(archive_path)
            combined_html = self.combineContentWithStyel()

            macro_body = f'''
            <ac:structured-macro ac:name="html">
                <ac:plain-text-body><![CDATA[{combined_html}]]></ac:plain-text-body>
            </ac:structured-macro>
            '''

            content = f"""
            <h1><strong>{self.boardName}</strong></h1>
            <a href="file://{archive_path}" download="{archive_filename}">{archive_filename}</a>
            {macro_body}
            """
        
        return content


if __name__ == "__main__":
    automate_report = AutomateReportOnCollab(r"D:\01_TOOL\tiger-robot\output")
    # automate_report.archiveFiles("JLR_VCM", r"D:\01_TOOL\tiger-robot\output")
    # automate_report.createDailySanityPage()
    # automate_report.getTestStatisticsContent()
    automate_report.updatePageBody()
