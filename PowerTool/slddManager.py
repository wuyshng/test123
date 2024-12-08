import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox
import json

def load_data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


class SlddManager():
    def __init__(self):
        super().__init__()

        self.data = load_data_from_json('sldd.json')
        self.Module = [_module["name"] for _module in self.data["Module"]]

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.university_label = QLabel("Select University:")
        layout.addWidget(self.university_label)

        self.university_combo = QComboBox()
        self.university_combo.addItems(self.universities)
        self.university_combo.currentIndexChanged.connect(self.on_university_select)
        layout.addWidget(self.university_combo)

        self.faculties_label = QLabel("Select Faculty:")
        layout.addWidget(self.faculties_label)

        self.faculties_combo = QComboBox()
        layout.addWidget(self.faculties_combo)

        self.setLayout(layout)

    def on_university_select(self, index):
        selected_university = self.university_combo.currentText()
        faculties = [faculty for uni in self.data["universities"] if uni["name"] == selected_university for faculty in uni["faculties"]]
        self.faculties_combo.clear()
        self.faculties_combo.addItems(faculties)