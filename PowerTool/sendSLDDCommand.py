import subprocess
from time import sleep
from commonVariable import *
class slddCommand():
    def __init__(self, deviceID = UNKNOWN_ID):
        self.testingDeviceID = deviceID

    def setDeviceID(self, deviceID):
        self.testingDeviceID = deviceID

    def send_adb_shell_command(self, command):
        if self.testingDeviceID == UNKNOWN_ID:
            adb_command = f"adb1 shell {command}"
        else:
            adb_command = f"""adb1 -s {self.testingDeviceID} shell "{command}\""""
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if process.returncode == 0:
            # print(f"Command '{command}' executed successfully.")
            if output:
                # print(output.decode())
                return output.decode()
        else:
            print(f"Error executing command '{command}'.")
            if error:
                print("Error message:")
                print(error.decode())
                return E_ERROR
        

    def getDeviceID(self):
        adb_command = f"adb1 devices"
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if output:
            output = output.decode()
        try:
            deviceID = output.split("\n")[1].split()[0]
        except Exception as e:
            # print("No device")
            deviceID = E_ERROR

        return deviceID

    def forwardLog(self):
        print("____________________Forward Logs_______________________")
        if self.testingDeviceID == UNKNOWN_ID:
            adb_command = f"adb1 forward tcp:3490 tcp:3490"
        else:
            adb_command = f"adb1 -s {self.testingDeviceID} forward tcp:3490 tcp:3490"
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

    def keepAlive(self):
        if self.testingDeviceID == UNKNOWN_ID:
            adb_command = f"adb1 shell sldd power input TEST_POWER_LOCK 1"
        else:
            adb_command = f"adb1 -s {self.testingDeviceID} shell sldd power input TEST_POWER_LOCK 1"
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

    def getListDeviceID(self):
        adb_command = f"adb1 devices"
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        deviceList = []
        if output:
            output = output.decode()
            deviceID = output.split("\n")
            for line in deviceID:
                if line.find('\t') != -1:
                    id = line.split('\t')
                    deviceList.append(id[0])
        return deviceList
    
    def getProcessID(self, serviceName):
        if self.testingDeviceID == UNKNOWN_ID:
            adb_command = f"""adb1 shell "ps -a | grep {serviceName}\""""
        else:
            adb_command = f"""adb1 -s {self.testingDeviceID} shell "ps -a | grep {serviceName}\""""
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if process.returncode == 0:
            # print(f"Command '{command}' executed successfully.")
            if output:
                # print(output.decode())
                tmp = output.decode().strip().split("\n")
                if (len(tmp) == 3):
                    ret = tmp[0].strip().split(" ")[0]
                    return ret
                else:
                    return E_ERROR
        else:
            print(f"Error executing command '{serviceName}'.")
            if error:
                print("Error message:")
                print(error.decode())
                return E_ERROR
    
    def verifyADBOutput(self, command, expectedOutput):
        if self.testingDeviceID == UNKNOWN_ID:
            adb_command = f"adb1 shell {command}"
        else:
            adb_command = f"""adb1 -s {self.testingDeviceID} shell "{command}\""""
        process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if process.returncode == 0:
            # print(f"Command '{command}' executed successfully.")
            if output:
                # print(output.decode())
                output = output.decode()
                print("output = f{output}")
                if expectedOutput in output:
                    return E_OK
        else:
            print(f"Error executing command '{command}'.")
            if error:
                print("Error message:")
                print(error.decode())
                return E_ERROR
        return E_ERROR

# Example command to send
if __name__ == '__main__':
    command_to_send = "sldd power state"  # List files in the /sdcard directory
    expectedOutput = "error"
    slddcmd = slddCommand()
    result = slddcmd.verifyADBOutput(command_to_send, expectedOutput)
    print(result)