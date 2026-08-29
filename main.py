import sys

from PySide6.QtWidgets import QApplication

from ui import MyApp


def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
