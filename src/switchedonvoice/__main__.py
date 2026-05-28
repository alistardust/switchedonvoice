"""Entry point: python -m switchedonvoice"""
import sys
import logging

from PySide6.QtWidgets import QApplication

from switchedonvoice.ui.main_window import MainWindow


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
