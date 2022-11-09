from serial.tools import list_ports
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QMessageBox
from PyQt5 import uic

from windows.cancel_dialog import CancelDialog
from windows.serial_connection_error_dialog import SerialConnectionErrorDialog
from utils.port_listener import PortListener
from utils.worker_thread import WorkerThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('windows/ui/main.ui', self)

        self.port = ""

        self.count = 0
        self.done = 0
        self.buttonsGroup = [
            self.plusButton, self.minusButton, self.plusFiveButton, self.minusFiveButton, self.startButton
        ]
        self.elementsGroup = [
            self.cancelButton, self.resumePauseButton, self.remainderLabel, self.doneLabel
        ]

        self.__initUI()

    def __initUI(self):
        self.setFixedSize(800, 550)
        for button in self.buttonsGroup:
            button.show()

        self.cycleNum.display(self.count)
        for element in self.remainderLabel, self.doneLabel, self.cancelButton, self.resumePauseButton:
            element.hide()

        self.updatePortList()
        self.portListener = PortListener()
        self.portListener.update.connect(self.updatePortList)

        self.__listenButtons()
        self.__center()

    def __listenButtons(self):
        operation_buttons = {
            1: self.plusButton,
            5: self.plusFiveButton,
            -1: self.minusButton,
            -5: self.minusFiveButton
        }
        for i in operation_buttons.keys():
            operation_buttons[i].clicked.connect(lambda s, x=i: self.__displayValueChange(x))

        action_buttons = {
            self.resumePauseButton: self.__pauseResume,
            self.cancelButton: self.__cancel,
            self.startButton: self.__start
        }
        for button, action in zip(action_buttons.keys(), action_buttons.values()):
            button.clicked.connect(action)

    def updatePortList(self):
        self.comboBox.clear()
        for port in list_ports.comports():
            self.comboBox.addItem(port.name)

    def __displayValueChange(self, arg):
        self.count += arg
        if 0 > self.count or 99 < self.count:
            self.count = 0 if self.count < 0 else 99
        self.cycleNum.setDigitCount(int(len(str(self.count))))
        self.cycleNum.display(self.count)

    def __start(self):
        if self.cycleNum.intValue() == 0:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Ошибка")
            dlg.setText("Количество циклов не задано.")
            dlg.exec()
            return

        if self.comboBox.currentText() == '':
            SerialConnectionErrorDialog().exec()
            return

        self.worker = WorkerThread(self.comboBox.currentText())
        self.worker.messageReceived.connect(self.__processBoardOutput)

        self.portListener.exit()

        for button in self.buttonsGroup:
            button.hide()
        self.comboBox.hide()
        self.portLabel.hide()

        for element in self.elementsGroup:
            element.show()
        self.doneLabel.setText(f'Выполнено циклов: {self.done}/{self.count}')

    def __processBoardOutput(self, text: str):
        if text == 'done':
            self.__displayValueChange(-1)

    def __pauseResume(self):
        if self.resumePauseButton.text() == "pause":
            self.resumePauseButton.setText("resume")  # TODO: add action (send message to board, ..., ...)
        else:
            self.resumePauseButton.setText("pause")

    def __cancel(self):
        self.dialog = CancelDialog()
        self.dialog.accepted.connect(self.__backToMainWindow)
        self.dialog.exec()

    def __backToMainWindow(self):
        self.dialog.accept()
        self.worker.exit()
        self.portListener.exiting = False
        self.portListener.start( )
        for element in self.elementsGroup:
            element.hide()

        for button in self.buttonsGroup:
            button.show()
        self.comboBox.show()
        self.portLabel.show()

    def __center(self):  # FIXME: rename
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
