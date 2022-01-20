"""
Utility functions used by rest of program
"""

import json
import os
import shutil
import sys
from datetime import datetime
from typing import List

from PyQt5.QtWidgets import QMessageBox


def get_directory() -> str:
    """
    Gets the directory of the python file or executable
    :return: directory of python file or executable
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)


def get_resources_dir() -> str:
    """
    :return: resources directory
    """
    return os.path.join(get_directory(), "Resources")


def get_data(field):
    """
    gets the specified value from data.json
    :param field: the key of the value to retrieve
    :return: the requested value
    """
    with open(os.path.join(get_directory(), "data.json")) as data_file:
        data = json.load(data_file)
    return data[field]


def get_entries_dir():
    """
    :return: the entries directory in the current journal
    """
    return os.path.join(get_data("journal_dir"), "entries")


def get_journal_dir():
    """
    :return: the current journal directory
    """
    return os.path.join(get_data("journal_dir"))


def get_attachments_dir():
    """
    :return: the attachments directory in the journal
    """
    return os.path.join(get_data("journal_dir"), "attachments")


def set_page_zoom(zoom: float):
    """
    :param zoom: the zoom level of the preview panel
    :return: None
    """
    set_data("page_zoom", zoom)


def get_page_zoom():
    """
    :return: the zoom level of preview panel
    """
    return get_data("page_zoom")


def get_splitter_sizes() -> List[int]:
    """
    :return: sizes of each splitter element
    """
    return get_data("splitter_sizes")


def set_splitter_sizes(state: List[int]) -> None:
    """
    :param state: sizes of each splitter element
    :return:
    """
    set_data("splitter_sizes", state)


def set_journal_dir(journal_dir) -> None:
    """
    :param journal_dir: path of current journal
    :return: None
    """
    set_data("journal_dir", journal_dir)


def get_toggle_states() -> List[bool]:
    """
    :return: whether each panel should be visible
    """
    return [get_data("toggle_selector"), get_data("toggle_editor"), get_data("toggle_preview")]


def set_toggle_states(states: List[bool]) -> None:
    """
    :param states: Whether each panel is currently visible
    :return: None
    """
    set_data("toggle_selector", states[0])
    set_data("toggle_editor", states[1])
    set_data("toggle_preview", states[2])


def set_data(field: str, value) -> None:
    """
    Sets the specified value in data.json
    :param field: the field to alter the value of
    :param value: the value to set
    :return: None
    """
    data = {}
    with open(os.path.join(get_directory(), "data.json"), "r") as data_file:
        data = json.load(data_file)
        data[field] = value
    with open(os.path.join(get_directory(), "data.json"), "w") as data_file_write:
        json.dump(data, data_file_write, indent=4)


def get_datetime_format() -> str:
    """
    :return: the format for datetime in entries
    """
    return get_data("datetime_format")


def get_editor_font_size():
    """
    :return: the font size of the markdown editor
    """
    return get_data("editor_font_size")


def get_seperator() -> str:
    """
    :return: the string to be inserted after each entry when exporting as a single file
    """
    return get_data("entry_seperator")


def replace_chars_for_file(file_name: str) -> str:
    """
    Replaces characters that should not be in a file name
    :param file_name: The string to replace characters in
    :return:
    """
    for char in (" ", "/", "\\", "|", ":"):
        file_name = file_name.replace(char, "_")
    return file_name

def attachment_reference(file_name: str) -> str:
    insert_text = "!" if os.path.splitext(file_name)[1].lower() in (".jpg", ".jpeg", ".png", ".gif") else ""
    insert_text += "[](../attachments/" + file_name + ")\n"
    return insert_text

def copy_files_to_attachments(files: list[str]):
    insert_text = ""
    for file in files:
        cur_datetime = datetime.now()
        file_name = cur_datetime.strftime(get_datetime_format()) + "_" + os.path.basename(file)
        file_name = replace_chars_for_file(file_name)
        shutil.copy2(file, os.path.join(get_attachments_dir(), file_name))
        insert_text += attachment_reference(file_name)

        # deletes the original file if it was in the attachments folder
        if os.path.abspath(os.path.dirname(file)) == os.path.abspath(get_attachments_dir()):
            os.remove(file)

    return insert_text

def alert_user(text: str) -> None:
    """
    Creates a message box
    :param text: the text to be displayed in the message box
    :return: None
    """
    message = QMessageBox(text=text)
    message.setWindowTitle("Journal")
    message.exec()
