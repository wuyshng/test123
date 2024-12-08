import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QMessageBox

class loadCANConfiguration:
    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text files (*.cfg);;All files (*.*)")

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]
                if selected_file:
                    print(f"Selected file: {selected_file}")
                    return selected_file
                else:
                    self.show_alert("Error", "Invalid file path selected.")
            else:
                self.show_alert("Error", "No file selected.")

    def show_alert(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
# internal test functions
if __name__ == '__main__':
    app = QApplication(sys.argv)
    filename = loadCANConfiguration()
    filename.open_file_dialog()

