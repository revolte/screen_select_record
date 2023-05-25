from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import time
import numpy as np
import pyautogui
import cv2


class CustomWindow(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event):
        # Create a QPainter object to draw on the widget
        painter = QPainter(self)

        # Set the pen color and width
        pen = QPen(Qt.red, 10)
        painter.setPen(pen)
        # Enable the painter's composition mode for blending with the background
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Draw a rectangle representing the border
        painter.drawRect(self.rect())


class ButtonWindow(QWidget):
    stopClicked = pyqtSignal()

    def __init__(self, app):
        super().__init__()

        # Set the title and window geometry
        screenGeometry = QDesktopWidget().screenGeometry()
        self.setWindowTitle("Stop")
        self.setGeometry(screenGeometry.width()-400, screenGeometry.height()-100, 300, 100)
        # Create a button in the button window
        button1 = QPushButton("Stop Recording", self)
        button1.setGeometry(0, 30, 180, 60)
        button1.setStyleSheet("color: green;")
        button1.setFont(QFont('Times', 10))
        button2 = QPushButton("Close All", self)
        button2.setGeometry(180, 30, 100, 60)
        button2.setStyleSheet("color: red;")
        button2.setFont(QFont('Times', 10))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        button2.clicked.connect(app.closeAllWindows)
        button1.clicked.connect(self.onButtonClicked)

        # Show the button window
        self.show()

    def onButtonClicked(self):
        self.stopClicked.emit()


class Worker(QThread):
    # finished = pyqtSignal()

    def __init__(self, region, video_file_name):
        super().__init__()
        self.region = region
        self.video_file_name = video_file_name

    def run(self):
        x, y, width, height = self.region
        print(f"Position (x, y, width, height): {x}, {y}, {width}, {height}")
        region = (x, y, width, height)
        if region is None:
            region = pyautogui.size()
        codec = cv2.VideoWriter_fourcc(*"XVID")

        w, h = width, height
        video_writer = cv2.VideoWriter(self.video_file_name, codec, 30, (w, h))
        time.sleep(2)

        while not self.isInterruptionRequested():
            img = pyautogui.screenshot(region=region)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_writer.write(frame)

        video_writer.release()
        self.finished.emit()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Get the screen's geometry
        self.region = None
        screenGeometry = QDesktopWidget().screenGeometry()

        # Calculate the center position of the window
        x = (screenGeometry.width() - self.width()) // 2
        y = (screenGeometry.height() - self.height()) // 2
        # set the title
        self.setWindowTitle("Screen Recording")

        # Create a custom window widget
        self.custom_window = CustomWindow()
        # setting the geometry of window
        self.setGeometry(60, 60, 600, 400)
        self.setCentralWidget(self.custom_window)
        self.setWindowOpacity(0.1)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Set the window border color to red
        self.setStyleSheet("QMainWindow { border: 12px solid red; }")
        # create a button
        self.button_start = QPushButton("Start Recording", self)
        self.button_start.setGeometry(0, 0, 200, 40)
        # Apply styles to the button
        self.button_start.setStyleSheet('''
                   QPushButton {
                       background-color: red;
                       color: white;
                       border: 6px solid #008CBA;
                       border-radius: 12px;
                       font-size: 25px;
                   }
                   QPushButton:hover {
                       background-color: bleu;
                   }
                   QPushButton:pressed {
                       background-color: #145714;
                   }
               ''')

        self.button_start.clicked.connect(self.startThread)

        self.button_stop = QPushButton("Stop", self)
        self.button_stop.setGeometry(100, 0, 100, 50)
        self.button_stop.setStyleSheet("color: red;")
        self.button_stop.setFont(QFont('Times', 15))
        self.button_stop.clicked.connect(self.stopThread)
        self.button_stop.setEnabled(False)
        self.button_stop.setHidden(True)
        # Create the button window and pass the reference to the QApplication instance
        self.button_window = ButtonWindow(qApp)
        self.button_window.stopClicked.connect(self.stopThread)

        # create the worker thread
        self.worker = None
        self.video_file_name = ""
        self.move(x, y)
        # show all the widgets
        self.show()

    def startThread(self):
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.window().showMinimized()
        x = self.geometry().x()
        y = self.geometry().y()
        width = self.geometry().width()
        height = self.geometry().height()
        self.region = (x, y, width, height)

        # Open the file dialog
        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter("AVI Files (*.avi)")

        if dialog.exec_() == QDialog.Accepted:
            self.video_file_name = dialog.selectedFiles()[0]
            self.worker = Worker(self.region, self.video_file_name)
            self.worker.finished.connect(self.threadFinished)
            self.worker.start()
        else:
            self.button_start.setEnabled(True)
            self.button_stop.setEnabled(False)

    def stopThread(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.showNormal()

    def threadFinished(self):
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        print("Thread finished.")


if __name__ == "__main__":
    # create pyqt5 app
    App = QApplication(sys.argv)

    # create the instance of our Window
    window = Window()

    # start the app event loop
    sys.exit(App.exec_())
