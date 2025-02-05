import os
import sys
from PySide6.QtWidgets import QApplication
from ui import MyApp
import PySide6

def main():
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
