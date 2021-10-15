"""
Editor for the markdown formatted entries
"""

import os
from typing import List

from PyQt5.QtCore import Qt, QRegularExpression, pyqtSignal
from PyQt5.QtGui import QTextCursor, QFont, QSyntaxHighlighter, QTextDocument, QTextCharFormat, QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QTextEdit, QListWidgetItem, QShortcut

import Utilities


class MarkdownEditor(QTextEdit):
    update_selector = pyqtSignal()

    def __init__(self, parent):
        super(MarkdownEditor, self).__init__(parent)
        self.frame_format = self.document().rootFrame().frameFormat()
        self.has_text_changed = False
        self.font = QFont()
        self.font.setFamily("Consolas")
        self.font.setPointSize(Utilities.get_editor_font_size())
        self.setFont(self.font)
        self.init_frame_format()
        self.setUndoRedoEnabled(True)
        self.setAcceptRichText(False)

        self.textChanged.connect(lambda: self.set_has_text_changed(True))

        # Shortcuts
        self.bold_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.bold_shortcut.activated.connect(lambda: self.emphasize_selected_text("**"))
        self.italics_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.italics_shortcut.activated.connect(lambda: self.emphasize_selected_text("*"))

    def get_has_text_changed(self) -> bool:
        return self.has_text_changed

    def set_has_text_changed(self, val: bool) -> None:
        self.has_text_changed = val

    def update_editor(self, current: QListWidgetItem) -> None:
        """
        Executes when a new entry is opened; Sets text to that entry
        :param selections: The current selected entry
        :return: None
        """
        if current:
            path_to_entry = os.path.join(Utilities.get_entries_dir(), current.text())
            if os.path.isfile(path_to_entry):
                with open(path_to_entry) as current_entry:
                    self.setPlainText(current_entry.read())
            else:
                Utilities.alert_user("Selected entry does not exist.")
                self.update_selector.emit()
        else:
            self.setPlainText("")
        self.init_frame_format()

    def init_frame_format(self) -> None:
        """
        Sets the margins of the editor
        :return: None
        """
        self.frame_format.setLeftMargin(30)
        self.frame_format.setRightMargin(30)
        self.frame_format.setTopMargin(30)
        self.document().rootFrame().setFrameFormat(self.frame_format)

    def update_margin(self, height: int) -> None:
        """
        Updates the bottom margin of the editor so that the user can scroll below the bottom of the text
        :param height: The height to set the bottom margin
        :return: None
        """
        self.frame_format.setBottomMargin(height)
        self.document().rootFrame().setFrameFormat(self.frame_format)

    def emphasize_selected_text(self, emphasis_text: str) -> None:
        """
        adds emphasis to selected text (italics or bold)
        :param emphasis_text: the text to be inserted before and after the selected text
        :return: None
        """
        cursor1 = self.textCursor()
        cursor2 = self.textCursor()

        cursor1.setPosition(min(cursor1.position(), cursor1.anchor()))
        cursor2.setPosition(max(cursor2.position(), cursor2.anchor()))

        cursor1.insertText(emphasis_text)
        pos1 = cursor1.position()
        cursor2.setKeepPositionOnInsert(True)
        cursor2.insertText(emphasis_text)
        cursor1.setPosition(pos1)           # keepPositionOnInsert doesn't work
        cursor1.setPosition(cursor2.position(), QTextCursor.MoveMode.KeepAnchor)
        cursor1.setKeepPositionOnInsert(False)
        self.setTextCursor(cursor1)


    def keyPressEvent(self, e: QKeyEvent) -> None:
        """
        Overrides keyPressEvent in order to insert new list elements and allow indenting lists with tab
        :param e: QKeyEvent
        :return: None
        """
        if e.text() == "\t":
            cursor = self.textCursor()
            # cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            # last_line = cursor.selectedText()
            last_line = cursor.block().text()
            last_line_strip = last_line.strip()
            if last_line_strip and (last_line_strip in ("*", "-", "+")) or (
                    last_line_strip[0:-1].isnumeric() and last_line_strip[-1] in (".", ")")):
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                if Qt.KeyboardModifier.ShiftModifier == e.modifiers() and last_line[0] == "\t":
                    cursor.deleteChar()
                else:
                    cursor.insertText("\t")
                return
        elif e.key() == Qt.Key_Return:
            cursor = self.textCursor()
            # cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            # last_line = cursor.selectedText()
            last_line = cursor.block().text()
            last_line_lstrip = last_line.lstrip()
            for marker in ("- [ ]", "*", "-", "+", ">"):
                if last_line_lstrip and last_line_lstrip.startswith(marker + " "):
                    to_insert = "\n" + last_line[0:last_line.index(marker)] + marker + " "
                    self.insertPlainText(to_insert)
                    return
            for num_marker in (".", ")"):
                if num_marker in last_line_lstrip and last_line_lstrip[
                                                      0:last_line_lstrip.index(num_marker)].isnumeric():
                    to_insert = "\n" + last_line[0:last_line.index(last_line_lstrip[0])] + str(
                        int(last_line_lstrip[0:last_line_lstrip.index(num_marker)]) + 1) + num_marker + " "
                    self.insertPlainText(to_insert)
                    return
        super().keyPressEvent(e)


# Not currently being used
class MarkdownSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super(MarkdownSyntaxHighlighter, self).__init__(document)
        self.formatting = {
            "h1": "^(.+)[ \t]*\n(=+|-+)[ \t]*\n+",
            "h2": "/^## (.*$)/gim",
            "h3": "/^### (.*$)/gim",
            "blockquote": "/^\> (.*$)/gim",
            "bold": "/\*\*(.*)\*\*/gim",
            "italics": "/\*(.*)\*/gim",
            "link": "/\[(.*?)\]\((.*?)\)/gim"
        }
        for key in self.formatting:
            expression = QRegularExpression(self.formatting[key])
            self.formatting[key] = expression

    def highlightBlock(self, text: str) -> None:
        format = QTextCharFormat()
        format.setFontWeight(QFont.Bold)

        iter = self.formatting["h1"].globalMatch(text)

        while iter.hasNext():
            next = iter.next()
            self.setFormat(next.capturedStart(), next.capturedLength(), format)
