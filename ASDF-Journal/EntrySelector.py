"""
List of entries in the journal that the user can select from
"""

import glob
import os
from datetime import datetime
from typing import List

from PyQt5.QtCore import QDate, Qt, QPoint
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidget, QAbstractItemView, QMenu, QAction, QListWidgetItem, QInputDialog

import Utilities


class EntrySelector(QListWidget):
    def __init__(self, parent):
        super(EntrySelector, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        font = QFont()
        font.setFamily("Verdana")
        font.setPointSize(14)
        self.setFont(font)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos: QPoint) -> None:
        global_pos = self.mapToGlobal(pos)

        context_menu = QMenu(self)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.rename_entry(self.currentItem()))
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_current_entry)
        context_menu.addAction(rename_action)
        context_menu.addAction(delete_action)

        context_menu.exec(global_pos)

    def rename_entry(self, entry: QListWidgetItem) -> None:
        name, confirm = QInputDialog.getText(self, "Rename Entry", "", text=entry.text())

        if confirm:
            os.rename(os.path.join(Utilities.get_entries_dir(), entry.text()),
                      os.path.join(Utilities.get_entries_dir(), name))
            entry.setText(name)

    def delete_current_entry(self) -> None:
        os.remove(os.path.join(Utilities.get_entries_dir(), self.currentItem().text()))
        self.takeItem(self.currentRow())

    def update_entry_selector(self) -> None:
        """
        Updates the entry selector when a new journal is opened
        :return: None
        """
        self.clear()
        entries_dir = Utilities.get_entries_dir()

        if not Utilities.get_journal_dir():
            return

        if not os.path.isdir(entries_dir):
            Utilities.alert_user("Selected folder does not contain a journal.")
            return

        for entry in sorted(glob.glob(os.path.join(entries_dir, "*.md")), reverse=True):

            entry_item = QListWidgetItem(self)
            entry_item.setText(os.path.splitext(os.path.basename(entry))[0].replace("_", " "))
            entry_item.setData(Qt.UserRole, entry)
            self.addItem(entry_item)

        if self.count():
            self.setCurrentRow(0)

    def current_entry_path(self):
        return self.currentItem().data(Qt.UserRole) if self.currentItem() else ""

    def navigate_direction(self, direction_up: bool) -> None:
        """
        Navigates one entry up or down; used by ketboard shortcuts
        :param direction_up: whether to go up or down
        :return: None
        """
        if direction_up and self.currentRow() > 0:
            self.setCurrentRow(self.currentRow() - 1)
        elif not direction_up and self.currentRow() < (self.count() - 1):
            self.setCurrentRow(self.currentRow() + 1)

    def get_all_entries(self) -> List[str]:
        """
        Gets all entries in current journal
        :return: list of file names
        """
        entries = []
        for entry in sorted(glob.glob(os.path.join(Utilities.get_entries_dir(), "*.md"))):
            entries.append(os.path.basename(entry))
        return entries

    def set_entry_date(self, date: QDate) -> None:
        """
        Opens the entry selected from the calendar
        :param date: The date selected in the calendar
        :return: None
        """
        calendar_datetime = datetime(date.year(), date.month(), date.day())
        formatted_datetime = Utilities.replace_chars_for_file(
            calendar_datetime.strftime(Utilities.get_datetime_format()))
        formatted_datetime_length = len(datetime.now().strftime(Utilities.get_datetime_format()))
        entries = sorted(glob.glob(os.path.join(Utilities.get_entries_dir(), "*.md")), reverse=True)
        for i in range(len(entries)):
            entries[i] = os.path.basename(entries[i])[0:formatted_datetime_length]

        if entries:
            i = len(entries) - 1
            while i > 0 and entries[i] < formatted_datetime:
                i -= 1
            self.setCurrentRow(i)
