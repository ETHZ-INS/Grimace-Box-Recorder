import sys
import os
from pathlib import Path

from PySide6 import QtGui
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

# Show splashscreen before the big module imports to show the user that something's happening
bundle_dir = getattr(sys, '_MEIPASS', os.getcwd())
res_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'res')))
splashscreen_image_file = res_folder / "splashscreen.png"
app_icon_file = res_folder / "logo.png"

app = QApplication(sys.argv)
pixmap = QPixmap(splashscreen_image_file)
splash = QSplashScreen(pixmap)
splash.show()

import logging.handlers

logger = logging.getLogger("grimace_recorder")
logger.setLevel(logging.DEBUG)

log_file = Path(os.getenv('LOCALAPPDATA')) / "Grimace Recorder" / "logs" / "grimace_recorder.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

# Switch to a new logfile every midnight, keep last 30 files
file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=30)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)


def uncaught_exception_handler(type, value, tb):
    logger.exception("Uncaught exception: %s", value, exc_info=(type, value, tb))


sys.excepthook = uncaught_exception_handler

logger.info("Starting Grimace Recorder")

from app.controller.grimace_box import MainWindow

window = MainWindow()
window.setWindowIcon(QtGui.QIcon(str(app_icon_file)))
window.show()
if splash is not None:
    splash.finish(window)

window.update_video_label_size()

sys.exit(app.exec())
