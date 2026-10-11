"""Launch CalcBook."""

import sys
from PyQt6.QtWidgets import QApplication
from calcbook.app import CalcBookWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CalcBook")
    window = CalcBookWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
