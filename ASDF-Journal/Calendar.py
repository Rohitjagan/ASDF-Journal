"""
Calendar for selecting entries by date
"""

from datetime import datetime
from typing import List

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtGui import QTextCharFormat, QCloseEvent
from PyQt5.QtWidgets import QCalendarWidget

import Utilities


class Calendar(QCalendarWidget):
    closed = pyqtSignal()

    def __init__(self, parent = None):
        super(Calendar, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setWindowTitle("Calendar")
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)

        for weekend in (Qt.DayOfWeek.Sunday, Qt.DayOfWeek.Saturday):
            self.setWeekdayTextFormat(weekend, self.weekdayTextFormat(Qt.DayOfWeek.Wednesday))

    def highlight_dates_with_entries(self, entries: List[str]) -> None:
        """
        Highlights the dates that contain at least one entry
        :param entries: List of file names of entries
        :return: None
        """
        datetime_format_file = Utilities.replace_chars_for_file(Utilities.get_datetime_format())
        length_formatted_date = len(datetime.now().strftime(datetime_format_file))
        text_format = QTextCharFormat()
        text_format.setFontWeight(100)
        text_format.setFontUnderline(True)

        for entry in entries:
            entry_datetime = datetime.strptime(entry[0:length_formatted_date], datetime_format_file)
            qdate = QDate(entry_datetime.year, entry_datetime.month, entry_datetime.day)
            self.setDateTextFormat(qdate, text_format)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Overrides closeEvent to hide the window instead of closing it
        :param event: QCloseEvent
        :return: None
        """
        self.closed.emit()
        self.hide()
        event.ignore()
