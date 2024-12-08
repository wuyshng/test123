import subprocess
import time
from pydlt import DltFileReader
import os
from enum import Enum

class Action(Enum):
    EQUAL = 1
    CONTAIN = 2

FILTER_FILE = 'filter.txt'
OUTPUT_FILE = 'output.txt'

class DltClient:
    def __init__(self) -> None:
        self.listProcess = []

    def clear_config(self):
        with open(FILTER_FILE, 'w') as file:
            file.write('')

    def config(self, apid, ctid):
        with open(FILTER_FILE, 'a') as file:
            if os.path.getsize(FILTER_FILE) != 0:
                file.write('\n')
            file.write(f'{apid} {ctid}')
        return

    def start(self, SERVICE_NAME):
        curDir = os.getcwd()
        files = os.listdir(curDir)
        for file in files:
            if file.startswith(SERVICE_NAME):
                file_path = os.path.join(curDir, file)
                os.remove(file_path)

        # Start write output to file
        try:
            print("_________________Save logs to file_____________________")
            cmd = f'./dlt/dlt_daemon/dlt-receive.exe -o {SERVICE_NAME}.dlt -f {FILTER_FILE} -c 100M localhost'
            subP = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.listProcess.append(subP)
        except Exception as e:
            print('Error occurred while executing ADB command: ' + str(e))

        return



    def check_expected(self, action, expected, payload):
        if action == Action.CONTAIN:
            if expected in payload:
                return True
        elif action == Action.EQUAL:
            cnt = 0
            if expected in payload:
                for s in expected.split():
                    if s in payload.split():
                        cnt = cnt + 1

                if cnt == len(expected.split()):
                    return True
        return False

    def printMsg(self, SERVICE_NAME):
        self.stop()
        print("-----------------------DLT LOG--------------------------")
        result = ""
        file = f'{SERVICE_NAME}.dlt'
        for msg in DltFileReader(file):
            payload = msg.payload._to_str()
            print(payload)
            result+=payload+"\n"
        return result

    def isContainExpectedLog(self, expected, SERVICE_NAME):
        result = False
        file = f'{SERVICE_NAME}.dlt'
        for msg in DltFileReader(file):
            payload = msg.payload._to_str()
            if expected in payload:
                result = True
                break
        return result

    def stop(self):
        for subP in self.listProcess:
            subP.terminate()

if __name__=='__main__':
    dlt = DltClient()
    dlt.check_equal('onNotifyExtValueChanged : from ID(who)=0x10 value[1] = 5555')