"""Canvas blocks: SpreadsheetBlock, TextBlock, EquationBlock."""

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QTextEdit, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class CellWidget(QFrame):
    """A single spreadsheet cell showing formula (top) and result (bottom)."""

    edited = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(0)

        self.formula_edit = QLineEdit()
        self.formula_edit.setFont(QFont("Consolas", 9))
        self.formula_edit.setPlaceholderText("")
        self.formula_edit.setStyleSheet(
            "QLineEdit { border: none; background: white; color: #333; }"
        )
        self.formula_edit.editingFinished.connect(self.edited.emit)

        self.result_label = QLabel()
        self.result_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.result_label.setStyleSheet("color: #0066cc; background: #f0f4ff; padding: 1px;")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.result_label.setMinimumHeight(18)

        layout.addWidget(self.formula_edit)
        layout.addWidget(self.result_label)

        self.setMinimumWidth(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    @property
    def formula(self):
        return self.formula_edit.text()

    @formula.setter
    def formula(self, value):
        self.formula_edit.setText(value)

    def set_result(self, value, error=None):
        if error:
            self.result_label.setText(f"ERR")
            self.result_label.setToolTip(error)
            self.result_label.setStyleSheet(
                "color: red; background: #fff0f0; padding: 1px;"
            )
        elif value is not None:
            text = str(value)
            if isinstance(value, float):
                text = f"{value:g}"
            self.result_label.setText(text)
            self.result_label.setToolTip(str(value))
            self.result_label.setStyleSheet(
                "color: #0066cc; background: #f0f4ff; padding: 1px;"
            )
        else:
            self.result_label.setText("")
            self.result_label.setToolTip("")
            self.result_label.setStyleSheet(
                "color: #0066cc; background: #f0f4ff; padding: 1px;"
            )


class SpreadsheetBlock(QFrame):
    """A named spreadsheet block with rows/columns and formula/result cells."""

    content_changed = pyqtSignal()

    def __init__(self, name="sheet1", rows=5, cols=5, parent=None):
        super().__init__(parent)
        self.block_name = name
        self.rows = rows
        self.cols = cols
        self.cells = {}  # (row, col) -> CellWidget

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("SpreadsheetBlock { background: white; border: 2px solid #888; }")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Name bar
        name_bar = QFrame()
        name_bar.setStyleSheet("background: #4a90d9; padding: 2px;")
        name_layout = QHBoxLayout(name_bar)
        name_layout.setContentsMargins(6, 2, 6, 2)
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: white;")
        name_layout.addWidget(self.name_label)
        name_layout.addStretch()
        outer_layout.addWidget(name_bar)

        # Grid area
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: white;")
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Column headers
        for c in range(cols):
            lbl = QLabel(chr(65 + c))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            lbl.setStyleSheet("background: #e0e0e0; border: 1px solid #ccc; padding: 2px;")
            lbl.setMinimumWidth(90)
            self.grid_layout.addWidget(lbl, 0, c + 1)

        # Row headers and cells
        for r in range(rows):
            lbl = QLabel(str(r + 1))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            lbl.setStyleSheet("background: #e0e0e0; border: 1px solid #ccc; padding: 2px;")
            lbl.setFixedWidth(30)
            self.grid_layout.addWidget(lbl, r + 1, 0)

            for c in range(cols):
                cell = CellWidget()
                cell.edited.connect(self.content_changed.emit)
                self.cells[(r, c)] = cell
                self.grid_layout.addWidget(cell, r + 1, c + 1)

        outer_layout.addWidget(grid_widget)

    def cell_ref(self, col_letter, row_number):
        """Get cell value by spreadsheet reference like 'A1'."""
        c = ord(col_letter.upper()) - 65
        r = row_number - 1
        cell = self.cells.get((r, c))
        if cell and cell.formula:
            return cell._last_result
        return None

    def execute(self, engine):
        """Evaluate all cells in this block, making results accessible as block_name[ref]."""
        results = {}
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[(r, c)]
                formula = cell.formula
                if formula:
                    result, error = engine.evaluate(formula)
                    cell.set_result(result, error)
                    cell._last_result = result
                    ref = f"{chr(65 + c)}{r + 1}"
                    results[ref] = result
                else:
                    cell.set_result(None)
                    cell._last_result = None

        # Make this block accessible in the namespace as a dict-like object
        engine.namespace[self.block_name] = CellAccessor(results)


class CellAccessor:
    """Allows referencing cells as sheet1['A1'] in formulas."""

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data.get(key.upper())

    def __repr__(self):
        return f"CellAccessor({self._data})"


class TextBlock(QFrame):
    """A free-form text block on the canvas."""

    content_changed = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setLineWidth(1)
        self.setStyleSheet("TextBlock { border: 1px solid #ccc; background: white; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Segoe UI", 11))
        self.text_edit.setPlaceholderText("Type text here...")
        self.text_edit.setStyleSheet("border: none;")
        self.text_edit.setMinimumHeight(60)
        self.text_edit.setMaximumHeight(200)
        if text:
            self.text_edit.setPlainText(text)
        self.text_edit.textChanged.connect(self.content_changed.emit)

        layout.addWidget(self.text_edit)

    def execute(self, engine):
        """Text blocks don't execute, but conform to the block interface."""
        pass


class EquationBlock(QFrame):
    """A single equation/expression with visible formula and result."""

    content_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("EquationBlock { background: transparent; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.formula_edit = QLineEdit()
        self.formula_edit.setFont(QFont("Consolas", 12))
        self.formula_edit.setPlaceholderText("Enter expression (e.g., 2*pi*r)")
        self.formula_edit.setStyleSheet(
            "QLineEdit { border: 1px solid #ddd; border-radius: 3px; "
            "padding: 4px 8px; background: white; }"
        )
        self.formula_edit.setMinimumWidth(300)
        self.formula_edit.editingFinished.connect(self.content_changed.emit)

        self.equals_label = QLabel("=")
        self.equals_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.equals_label.setStyleSheet("color: #666;")

        self.result_label = QLabel()
        self.result_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.result_label.setStyleSheet(
            "color: #0066cc; border: 1px solid #ddd; border-radius: 3px; "
            "padding: 4px 8px; background: #f0f4ff; min-width: 120px;"
        )
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.formula_edit, stretch=3)
        layout.addWidget(self.equals_label)
        layout.addWidget(self.result_label, stretch=2)

    @property
    def formula(self):
        return self.formula_edit.text()

    def execute(self, engine):
        """Evaluate the expression and display the result."""
        formula = self.formula
        if formula:
            result, error = engine.evaluate(formula)
            if error:
                self.result_label.setText(f"Error: {error}")
                self.result_label.setStyleSheet(
                    "color: red; border: 1px solid #ddd; border-radius: 3px; "
                    "padding: 4px 8px; background: #fff0f0; min-width: 120px;"
                )
            elif result is not None:
                text = f"{result:g}" if isinstance(result, float) else str(result)
                self.result_label.setText(text)
                self.result_label.setStyleSheet(
                    "color: #0066cc; border: 1px solid #ddd; border-radius: 3px; "
                    "padding: 4px 8px; background: #f0f4ff; min-width: 120px;"
                )
            else:
                self.result_label.setText("")
        else:
            self.result_label.setText("")
