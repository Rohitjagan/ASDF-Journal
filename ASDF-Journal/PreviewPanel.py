"""
Preview panel that renders the markdown code in the editor
"""

import os

import markdown
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

import Utilities


class PreviewPanel(QWebEngineView):
    def __init__(self, parent):
        super(PreviewPanel, self).__init__(parent)
        self.setPage(WebEnginePage(self))
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.html_code = ""
        self.placeholder_path = None
        self.init_html()
        self.markdown = markdown.Markdown(
            extensions=["markdown.extensions.abbr", "markdown.extensions.attr_list", "markdown.extensions.def_list",
                        "markdown.extensions.fenced_code", "markdown.extensions.footnotes",
                        "markdown.extensions.md_in_html", "markdown.extensions.tables"])
        self.setHtml(self.html_code.format(""), self.placeholder_path)
        if Utilities.get_page_zoom():
            self.page().setZoomFactor(Utilities.get_page_zoom())

    def init_html(self) -> None:
        """
        Sets the default html code; executes whenever a new journal is opened
        :return: None
        """
        css_path = os.path.join(Utilities.get_resources_dir(), "style.css")
        self.html_code = '<!DOCTYPE html>\n<html>\n<head>\n\t<link rel="stylesheet" href="' + css_path + '">\n</head>\n<body>\n{}\n</body>\n</html>'
        # Needed so that attachment links work in the preview
        self.placeholder_path = QUrl.fromLocalFile(os.path.join(Utilities.get_entries_dir(), "placeholder.txt"))

    def update_preview(self, text, at_end: bool = False) -> None:
        """
        Updates the preview with the current text in the editor and scrolls to the bottom if the user added to the end
        of the document
        :param text: The markdown text to be rendered
        :param at_end: if the user added to the end of the document
        :return: None
        """
        self.setHtml(self.html_code.format(self.markdown.reset().convert(text)), self.placeholder_path)
        if at_end:
            self.page().runJavaScript("window.scrollTo(0,document.body.scrollHeight);")


class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        """
        Overrides method to open links in system default browser instead of in the preview
        """
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True
