"""
Main interface/window for program
"""

import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import List

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QKeySequence, QCloseEvent, QIcon, QResizeEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QMenuBar, QMenu, QAction, QSplitter, QFileDialog, \
    QInputDialog, QMessageBox, QShortcut, QSizePolicy

import Utilities
from Calendar import Calendar
from EntrySelector import EntrySelector
from MarkdownEditor import MarkdownEditor
from PreviewPanel import PreviewPanel


class MainInterface(QMainWindow):

    def __init__(self):
        super(MainInterface, self).__init__()
        self.setWindowTitle("Journal")
        self.splitter = QSplitter(self)

        self.entry_selector = EntrySelector(self)
        self.splitter.addWidget(self.entry_selector)

        self.markdown_editor = MarkdownEditor(self)
        self.splitter.addWidget(self.markdown_editor)

        self.preview_panel = PreviewPanel(self)
        self.splitter.addWidget(self.preview_panel)

        self.calendar = Calendar(self)
        self.calendar_action = None

        if Utilities.get_splitter_sizes():
            self.splitter.setSizes(Utilities.get_splitter_sizes())
        else:
            self.splitter.setSizes([200, 500, 500])
        self.setCentralWidget(self.splitter)
        self.entry_selector.setHidden(not Utilities.get_toggle_states()[0])
        self.markdown_editor.setHidden(not Utilities.get_toggle_states()[1])
        self.preview_panel.setHidden(not Utilities.get_toggle_states()[2])
        self.update_selector()

        self.menu_bar = QMenuBar()
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setFloatable(False)
        self.create_menu()

        # Create Shortcuts
        self.nav_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self)
        self.nav_up_shortcut.activated.connect(lambda: self.entry_selector.navigate_direction(True))
        self.nav_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self)
        self.nav_down_shortcut.activated.connect(lambda: self.entry_selector.navigate_direction(False))

        self.setup_connections()
        self.markdown_editor.update_editor(self.entry_selector.selectedItems())

        # For updating the preview panel
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.timer_updated)
        self.update_timer.start(1000)

    def create_menu(self) -> None:
        file_menu = QMenu("&File", self)
        open_journal_action = self.create_menu_action("&Open Journal", self.open_journal, "Ctrl+O", icon="open.svg")
        file_menu.addAction(open_journal_action)
        self.toolbar.addAction(open_journal_action)
        file_menu.addAction(
            self.create_menu_action("Open Journal in File Explorer", self.open_journal_folder, "Ctrl+Shift+O"))
        file_menu.addAction(self.create_menu_action("New Journal", self.new_journal))
        new_entry_action = self.create_menu_action("&New Entry", self.new_entry, "Ctrl+N", icon="write.svg")
        file_menu.addAction(new_entry_action)
        self.toolbar.addAction(new_entry_action)
        save_action = self.create_menu_action("&Save", self.save_entry, "Ctrl+S", icon="save.svg")
        file_menu.addAction(save_action)
        self.toolbar.addAction(save_action)
        file_menu.addAction(self.create_menu_action("&Exit", self.exit_interface))
        self.menu_bar.addMenu(file_menu)

        edit_menu = QMenu("&Edit", self)
        import_attachments_action = self.create_menu_action("&Import Attachments", self.import_attachments, "Ctrl+I",
                                                            icon="import.svg")
        edit_menu.addAction(import_attachments_action)
        self.toolbar.addAction(import_attachments_action)
        existing_attachments_action = self.create_menu_action("Add Existing Attachment", self.add_existing_attachments,
                                                              "Ctrl+Shift+I", icon="attachments.svg")
        edit_menu.addAction(existing_attachments_action)
        self.toolbar.addAction(existing_attachments_action)
        self.menu_bar.addMenu(edit_menu)

        spacerL = QWidget()
        spacerL.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacerL)

        view_menu = QMenu("&View", self)
        toggle_selector_action = self.create_menu_action("Entry Selector", self.toggle_entry_selector, "Ctrl+1",
                                                         checkable=True,
                                                         checked_state=(not self.entry_selector.isHidden()),
                                                         icon="selector.svg")
        view_menu.addAction(toggle_selector_action)
        self.toolbar.addAction(toggle_selector_action)
        toggle_editor_action = self.create_menu_action("Markdown Editor", self.toggle_markdown_editor, "Ctrl+2",
                                                       checkable=True,
                                                       checked_state=(not self.markdown_editor.isHidden()),
                                                       icon="editor.svg")
        view_menu.addAction(toggle_editor_action)
        self.toolbar.addAction(toggle_editor_action)
        toggle_preview_action = self.create_menu_action("HTML Preview", self.toggle_preview_panel, "Ctrl+3",
                                                        checkable=True,
                                                        checked_state=(not self.preview_panel.isHidden()),
                                                        icon="preview.svg")
        view_menu.addAction(toggle_preview_action)
        self.toolbar.addAction(toggle_preview_action)
        self.calendar_action = self.create_menu_action("Calendar", self.toggle_calendar, "Ctrl+Shift+C", checkable=True,
                                                       checked_state=False, icon="calendar.svg")
        view_menu.addAction(self.calendar_action)
        self.toolbar.addAction(self.calendar_action)
        self.menu_bar.addMenu(view_menu)

        spacerR = QWidget()
        spacerR.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacerR)

        export_menu = QMenu("&Export", self)
        export_action = self.create_menu_action("Export as single markdown file", self.export_single_file,
                                                icon="export.svg")
        export_menu.addAction(export_action)
        self.toolbar.addAction(export_action)
        self.menu_bar.addMenu(export_menu)

        self.setMenuBar(self.menu_bar)

    def create_menu_action(self, name: str, function, shortcut: str = None, checkable: bool = False,
                           checked_state: bool = False, icon: str = None) -> QAction:
        """
        Creates a QAction object for the menu and toolbar
        :param name: name of action
        :param function: function to be called when action is executed
        :param shortcut: keyboard shortcut
        :param checkable: whether action is toggleable
        :param checked_state: whether action should start toggled
        :param icon: icon image file
        :return: None
        """
        action = QAction(name, self)
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked_state)
            action.toggled.connect(lambda: function(action.isChecked()))
        else:
            action.triggered.connect(function)
        if shortcut:
            action.setShortcut(shortcut)
        if icon:
            action.setIcon(QIcon(os.path.join(Utilities.get_resources_dir(), "Icons", icon)))
        return action

    def setup_connections(self) -> None:
        """
        Initializes connections between widgets
        :return: None
        """
        self.entry_selector.itemSelectionChanged.connect(
            lambda: self.markdown_editor.update_editor(self.entry_selector.selectedItems()))
        self.entry_selector.itemSelectionChanged.connect(lambda: self.timer_updated())
        self.markdown_editor.update_selector.connect(self.update_selector)
        self.calendar.selectionChanged.connect(
            lambda: self.entry_selector.calendar_date_changed(self.calendar.selectedDate()))
        self.calendar.closed.connect(lambda: self.toggle_calendar(False))

    def open_journal(self) -> None:
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Journal Folder", Utilities.get_journal_dir(),
                                                           QFileDialog.ShowDirsOnly)
        if (selected_folder):
            Utilities.set_journal_dir(selected_folder)
            self.update_selector()
            self.preview_panel.init_html()

    def open_journal_folder(self) -> None:
        """
        Opens journal folder in system file viewer
        :return: None
        """
        if sys.platform == "win32":
            os.startfile(Utilities.get_journal_dir())
        elif sys.platform == "darwin":
            subprocess.Popen(["open", Utilities.get_journal_dir()])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", Utilities.get_journal_dir()])
        else:
            Utilities.alert_user("Unsupported platform.")

    def new_journal(self) -> None:
        """
        Creates a new journal in the selected folder
        :return: None
        """
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Location for New Journal",
                                                           Utilities.get_journal_dir(), QFileDialog.ShowDirsOnly)
        if (selected_folder):
            # selected_folder = folder_select.selectedFiles()[0]
            journal_name, confirm = QInputDialog.getText(self, "New Journal", "Journal Name:")
            if confirm:
                journal_dir = os.path.join(selected_folder, journal_name)
                os.makedirs(journal_dir, exist_ok=True)
                os.makedirs(os.path.join(journal_dir, "entries"), exist_ok=True)
                os.makedirs(os.path.join(journal_dir, "attachments"), exist_ok=True)
                Utilities.set_journal_dir(journal_dir)
                self.update_selector()

    def save_entry(self) -> None:
        """
        Saves the current entry
        :return: None
        """
        if len(self.entry_selector.selectedItems()) > 0:
            path_to_entry = os.path.join(Utilities.get_entries_dir(), self.entry_selector.selectedItems()[0].text())
            if os.path.isfile(path_to_entry):
                with open(os.path.join(Utilities.get_entries_dir(), self.entry_selector.selectedItems()[0].text()),
                          "w") as entry:
                    entry.write(self.markdown_editor.toPlainText())
            else:
                Utilities.alert_user("Selected entry does not exist.")

        else:
            Utilities.alert_user("Could not save because no note is selected.")

    def new_entry(self) -> None:
        """
        Adds a new entry to the journal
        :return: None
        """
        entries_dir = Utilities.get_entries_dir()
        cur_datetime = datetime.now()
        entry_name = cur_datetime.strftime(Utilities.get_datetime_format())

        title, confirm = QInputDialog.getText(self, "New Entry", "Entry Title (or leave blank):")
        if confirm:
            if title:
                entry_name += " " + title
            entry_name_file = Utilities.replace_chars_for_file(entry_name) + ".md"
            with open(os.path.join(entries_dir, entry_name_file), 'x') as entry:
                entry.writelines(["# " + entry_name + "\n"])
            self.update_selector()

    def import_attachments(self) -> None:
        """
        Adds a new attachment to the attachments folder and links it the entry
        :return: None
        """
        selected_files = QFileDialog.getOpenFileNames(self, "Select attachments to import")
        if selected_files:
            for selected_file in selected_files[0]:
                cur_datetime = datetime.now()
                file_name = cur_datetime.strftime(Utilities.get_datetime_format()) + "_" + os.path.basename(
                    selected_file)
                file_name = Utilities.replace_chars_for_file(file_name)
                shutil.copy2(selected_file, os.path.join(Utilities.get_attachments_dir(), file_name))
                insert_text = "!" if os.path.splitext(file_name)[1].lower() in (".jpg", ".jpeg", ".png", ".gif") else ""
                insert_text += "[](../attachments/" + file_name + ") "
                self.markdown_editor.insertPlainText(insert_text)

    def add_existing_attachments(self) -> None:
        """
        Links selected attachment from the attachments folder
        :return: None
        """
        selected_files = QFileDialog.getOpenFileNames(self, "Select attachments", Utilities.get_attachments_dir())
        if selected_files:
            for selected_file in selected_files[0]:
                file_name = os.path.basename(str(selected_file))
                insert_text = "!" if os.path.splitext(file_name)[1].lower() in (".jpg", ".jpeg", ".png", ".gif") else ""
                insert_text += "[](../attachments/" + file_name + ") "
                self.markdown_editor.insertPlainText(insert_text)

    def exit_interface(self) -> None:
        self.close()

    def toggle_entry_selector(self, checked: bool, action: QAction) -> None:
        action.setChecked(checked)
        if checked:
            self.entry_selector.show()
        else:
            self.entry_selector.hide()

    def toggle_markdown_editor(self, checked: bool, action: QAction) -> None:
        action.setChecked(checked)
        if checked:
            self.markdown_editor.show()
        else:
            self.markdown_editor.hide()

    def toggle_preview_panel(self, checked: bool, action: QAction) -> None:
        action.setChecked(checked)
        if checked:
            self.preview_panel.show()
        else:
            self.preview_panel.hide()

    def update_selector(self) -> None:
        """
        Updates the entry selector to the current journal folder
        :return: None
        """
        self.entry_selector.update_entry_selector()
        self.setWindowTitle("Journal - " + os.path.basename(Utilities.get_journal_dir()))
        self.calendar.highlight_dates_with_entries(self.entry_selector.get_all_entries())

    def toggle_calendar(self, checked: bool) -> None:
        """
        Toggles the calendar window
        :param checked: whether the calendar was turned on or off
        :return: None
        """
        self.calendar_action.setChecked(checked)
        if checked and self.calendar.isHidden():
            self.calendar.show()
            self.calendar.highlight_dates_with_entries(self.entry_selector.get_all_entries())
        else:
            self.calendar.hide()

    def export_single_file(self) -> None:
        """
        Exports the journal as a single markdown folder along with attachments
        :return: None
        """
        entries = self.entry_selector.get_all_entries()
        seperator = Utilities.get_seperator()
        export_path = QFileDialog.getExistingDirectory(self, "Export File", Utilities.get_journal_dir())
        export_file_path = os.path.join(export_path, os.path.basename(Utilities.get_journal_dir()), "journal")
        attachments_path = os.path.join(export_path, os.path.basename(Utilities.get_journal_dir()), "attachments")
        os.makedirs(export_file_path, exist_ok=True)
        os.makedirs(attachments_path, exist_ok=True)
        with open(os.path.join(export_file_path, "combined_journal.md"), 'w') as export_file:
            for entry in entries:
                with open(os.path.join(Utilities.get_entries_dir(), entry), 'r') as entry_file:
                    lines = entry_file.readlines()
                export_file.write(seperator)
                export_file.writelines(lines)
        for attachment in glob.glob(os.path.join(Utilities.get_attachments_dir(), "*")):
            shutil.copy2(attachment, os.path.join(attachments_path, os.path.basename(attachment)))

    def timer_updated(self) -> None:
        """
        Executes every time the timer is triggered; Updates the preview panel based on current text in the editor
        :return: None
        """
        if self.markdown_editor.get_has_text_changed():
            text = self.markdown_editor.toPlainText()
            self.preview_panel.update_preview(text, self.markdown_editor.textCursor().atEnd())
            self.markdown_editor.set_has_text_changed(False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Overrides the resizeEvent method in order to update the bottom margin of the editor (so that the user can scroll
        past the bottom)
        :param event: QReizeEvent
        :return: None
        """
        self.markdown_editor.update_margin(self.splitter.height())
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Overrides closeEvent method in order to store current state
        :param event: QCloseEvent
        :return: None
        """
        Utilities.set_page_zoom(self.preview_panel.page().zoomFactor())
        Utilities.set_splitter_sizes(self.splitter.sizes())
        Utilities.set_toggle_states([not self.entry_selector.isHidden(), not self.markdown_editor.isHidden(),
                                     not self.preview_panel.isHidden()])
        if self.entry_selector.currentItem():
            path_to_entry = os.path.join(Utilities.get_entries_dir(), self.entry_selector.currentItem().text())
            if os.path.isfile(path_to_entry):
                with open(path_to_entry) as entry:
                    if entry.read() != self.markdown_editor.toPlainText():
                        reply = QMessageBox.question(self, "Save Changes",
                                                     "Your changes have not been saved. Are you sure you want to exit?",
                                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        if reply == QMessageBox.No:
                            event.ignore()
                            return
        event.accept()
