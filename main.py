import json
import os.path
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

import Utilities
from MainInterface import MainInterface

def main():
    if not os.path.isfile(os.path.join(Utilities.get_directory(), "data.json")):
        data_json = {
            "journal_dir": "",
            "page_zoom": 1,
            "splitter_sizes": [],
            "toggle_selector": True,
            "toggle_editor": True,
            "toggle_preview": True,
            "datetime_format": "%Y-%m-%d %H%M",
            "editor_font_size": 12,
            "entry_seperator": "\n\n-----\n-----\n\n"
        }
        with open(os.path.join(Utilities.get_directory(), "data.json"), "w") as data_file:
            json.dump(data_json, data_file, indent=4)

    app = QApplication([])
    app.setWindowIcon(QIcon("Resources/Icons/journal-icon.png"))
    app.setStyle("Fusion")

    interface = MainInterface()
    interface.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
