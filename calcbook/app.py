"""Main CalcBook application window."""

import getpass
from datetime import date

from PyQt6.QtWidgets import (
    QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QToolBar, QSizePolicy, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction, QKeySequence

from .blocks import SpreadsheetBlock, TextBlock, EquationBlock
from .engine import ExecutionEngine


class CalcBookWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CalcBook")
        self.setMinimumSize(900, 700)

        self.engine = ExecutionEngine()
        self.block_widgets = []  # ordered list of block widgets on canvas

        self._build_toolbar()
        self._build_canvas()
        self._add_initial_content()

    def _build_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        run_action = QAction("Run All (F5)", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self._run_all)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        add_sheet = QAction("+ Spreadsheet", self)
        add_sheet.triggered.connect(self._add_spreadsheet_block)
        toolbar.addAction(add_sheet)

        add_eq = QAction("+ Equation", self)
        add_eq.triggered.connect(self._add_equation_block)
        toolbar.addAction(add_eq)

        add_text = QAction("+ Text", self)
        add_text.triggered.connect(self._add_text_block)
        toolbar.addAction(add_text)

    def _build_canvas(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background: #f8f8f8; border: none; }")

        self.canvas = QWidget()
        self.canvas.setStyleSheet("background: #f8f8f8;")
        self.canvas_layout = QVBoxLayout(self.canvas)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.canvas_layout.setContentsMargins(40, 20, 40, 40)
        self.canvas_layout.setSpacing(16)

        scroll.setWidget(self.canvas)
        self.setCentralWidget(scroll)

    def _add_initial_content(self):
        # Title
        self.title_edit = QLineEdit("Untitled Calculation")
        self.title_edit.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title_edit.setStyleSheet(
            "QLineEdit { border: none; border-bottom: 2px solid #4a90d9; "
            "background: transparent; padding: 4px; }"
        )
        self.title_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.canvas_layout.addWidget(self.title_edit)

        # Metadata
        meta_widget = QWidget()
        meta_layout = QHBoxLayout(meta_widget)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(20)

        date_label = QLabel(f"Date: {date.today().isoformat()}")
        date_label.setFont(QFont("Segoe UI", 10))
        date_label.setStyleSheet("color: #666;")

        try:
            username = getpass.getuser()
        except Exception:
            username = "Unknown"
        author_label = QLabel(f"Author: {username}")
        author_label.setFont(QFont("Segoe UI", 10))
        author_label.setStyleSheet("color: #666;")

        meta_layout.addWidget(date_label)
        meta_layout.addWidget(author_label)
        meta_layout.addStretch()
        self.canvas_layout.addWidget(meta_widget)

        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #ddd;")
        self.canvas_layout.addWidget(sep)

        # Default spreadsheet block
        self._add_spreadsheet_block(name="sheet1")

    def _add_spreadsheet_block(self, name=None):
        if name is None:
            n = sum(1 for b in self.block_widgets if isinstance(b, SpreadsheetBlock)) + 1
            name = f"sheet{n}"
        block = SpreadsheetBlock(name=name)
        block.content_changed.connect(self._run_all)
        self.canvas_layout.addWidget(block)
        self.block_widgets.append(block)
        self.engine.register_block(block)

    def _add_equation_block(self):
        block = EquationBlock()
        block.content_changed.connect(self._run_all)
        self.canvas_layout.addWidget(block)
        self.block_widgets.append(block)
        self.engine.register_block(block)

    def _add_text_block(self):
        block = TextBlock()
        self.canvas_layout.addWidget(block)
        self.block_widgets.append(block)
        # Text blocks don't trigger re-execution

    def _run_all(self):
        """Re-execute all blocks top to bottom."""
        self.engine.run_all()
