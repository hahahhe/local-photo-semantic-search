import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():

    app = QApplication(sys.argv)
    app.setApplicationName("LocalPhotoSearch")
    app.setOrganizationName("LocalPhotoSearch")

    window = MainWindow()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()