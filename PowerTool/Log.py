
from datetime import datetime

class Logger():
    def __init__(self):
        self.file_path = "Testing_Logs.txt"

    def Log(self, message):
        print(message)
        with open(self.file_path , 'a') as file:
            current_datetime = datetime.now()
            file.write(f"[{current_datetime}]:  ")
            file.write(f"{message}\n\n")

    def clearLogs(self):
        with open(self.file_path, 'w') as file:
            file.truncate()

