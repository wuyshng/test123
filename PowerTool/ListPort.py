import sys
from PyQt5 import QtWidgets, QtCore
import serial.tools.list_ports

class COMPortWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Available COM Ports')
        layout = QtWidgets.QVBoxLayout()

        com_ports_label = QtWidgets.QLabel('Available COM Ports:')
        layout.addWidget(com_ports_label)

        self.com_ports_combobox = QtWidgets.QComboBox()
        self.com_ports_combobox.currentIndexChanged.connect(self.update_port_info)
        layout.addWidget(self.com_ports_combobox)

        self.port_info_textedit = QtWidgets.QTextEdit()
        layout.addWidget(self.port_info_textedit)

        # Populate the ComboBox with available COM ports
        self.update_ports()

        self.setLayout(layout)

        # Setup a timer to periodically check for available ports
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_ports)
        self.timer.start(10000)  # Update every 10 seconds

    def update_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        current_port = self.com_ports_combobox.currentText()

        self.com_ports_combobox.clear()  # Clear the items in the combobox
        self.com_ports_combobox.addItems(ports)

        if current_port in ports:
            self.com_ports_combobox.setCurrentText(current_port)
        else:
            self.port_info_textedit.clear()

        # Check for Arduino port
        arduino_port = self.detect_arduino_port(ports)
        if arduino_port:
            self.com_ports_combobox.setCurrentText(arduino_port)

    def update_port_info(self):
        selected_port = self.com_ports_combobox.currentText()
        self.port_info_textedit.setPlainText(f"Selected Port: {selected_port}")

    def detect_arduino_port(self, ports):
        for port in ports:
            port_info = serial.tools.list_ports.comports()
            if "CH" in port_info:
                return port
            else:
                self.port_info_textedit.setPlainText(f"Selected Port: NO ARDUINO PORT")
        return None

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = COMPortWidget()
    window.show()
    sys.exit(app.exec_())