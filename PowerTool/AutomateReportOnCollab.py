import os
import shutil
from datetime import datetime
from commonVariable import *
from atlassian import Confluence
from playwright.sync_api import sync_playwright

class AutomateReportOnCollab:
    def __init__(self):
        self.isError = ""
        self.content = ""
        try:
            self.confluence = Confluence(url=COLLAB_BASE_URL, token=PAT)

            sourceDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.outputDir = os.path.join(sourceDir, "output")
        except Exception as e:
            print(f"Error: {e}")

    def getSanityResultFiles(self, boardName):
        if boardName in FILE_NAMES:
            return FILE_NAMES[boardName]
        else:
            raise ValueError(f"Can not found in files with {boardName}")

    def storeResultFiles(self, boardName):
        current_date = datetime.now().strftime("%Y%m%d")
        new_folder = f"{boardName}_{current_date}"
        new_folder_path = os.path.join(TEST_REPORT_PATH, new_folder)
        os.makedirs(new_folder_path, exist_ok=True)

        log_html_path = os.path.join(self.outputDir, "log.html")
        report_html_path = os.path.join(self.outputDir, "report.html")

        shutil.copy(log_html_path, new_folder_path)
        shutil.copy(report_html_path, new_folder_path)

        report_html_new_path = os.path.join(new_folder_path, "report.html")
        return report_html_new_path

    def authenticatePage(self):
        try:
            result = self.confluence.page_exists(space=COLLAB_SPACE, title=PARENT_PAGE_TITLE)
            return result
        except Exception as e:
            print(f"Error: {e}")

    def createDailySanityPage(self):
        if not self.authenticatePage():
            print("Page not found.")
            return False
        
        try:
            self.parentPageID = self.confluence.get_page_id(space=COLLAB_SPACE, title=PARENT_PAGE_TITLE)
            self.newPageTitle = self.getNewPageTitle()
            page = self.confluence.get_page_by_title(space=COLLAB_SPACE, title=self.newPageTitle)
            if not page:
                page = self.confluence.create_page(space=COLLAB_SPACE, title=self.newPageTitle, body="", parent_id=self.parentPageID)
            self.page_id = page['id']
            
        except Exception as e:
            print(f"Failed to create page: {e}")

    def updateDailySanityPage(self, boardName):
        self.boardName = boardName
        if self.isError == "":
            report_file_path = self.storeResultFiles(self.boardName)
            self.content += self.updatePageBody(report_file_path)
            self.confluence.update_page(page_id=self.page_id, title=self.newPageTitle, body=self.content, parent_id=self.parentPageID)
        else:
            self.content += f"""
            <h1><strong>{self.boardName}</strong></h1>
            <p>{self.isError}</p>
            """
            self.confluence.update_page(page_id=self.page_id, title=self.newPageTitle, body=self.content, parent_id=self.parentPageID)

    def getNewPageTitle(self):
        current_date = datetime.now().strftime("%Y%m%d")
        return f"Daily sanity test {current_date}"
    
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
        
    def combineContentWithStyle(self):
        content = self.getTestStatisticsContent()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_file_path = os.path.join(current_dir, STYLE_FILE_NAME)

        if not os.path.exists(style_file_path):
            raise FileNotFoundError(f"Style file not found: {style_file_path}")
        
        with open(style_file_path, "r", encoding="utf-8") as style_file:
            style_content = style_file.read()

        combined_html = f"""
            {style_content}
            {content}
        """
        return combined_html
    
    def updatePageBody(self, report_file_path):
        combined_html = self.combineContentWithStyle()

        macro_body = f'''
        <ac:structured-macro ac:name="html">
            <ac:plain-text-body><![CDATA[{combined_html}]]></ac:plain-text-body>
        </ac:structured-macro>
        '''

        content = f"""
        <h1><strong>{self.boardName}</strong></h1>
        <p>file:{report_file_path}</p>
        {macro_body}
        """
        return content

# if __name__ == "__main__":
#     automate_report = AutomateReportOnCollab()
#     automate_report.createDailySanityPage()
#     automate_report.updateDailySanityPage(JLR_TCUA)
#     automate_report.updateDailySanityPage(JLR_VCM)
