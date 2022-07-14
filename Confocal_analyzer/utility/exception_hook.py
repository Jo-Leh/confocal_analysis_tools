import traceback
from PyQt5 import QtWidgets

class ErrorMessage(QtWidgets.QMessageBox):
	def __init__(self, msg, info_text='', parent=None):
		super().__init__(parent)
		self.setWindowTitle('ERROR - ODMR')
		self.setIcon(QtWidgets.QMessageBox.Warning)
		self.setStandardButtons(QtWidgets.QMessageBox.Ok)
		self.setText(msg)
		if info_text:
			self.setInformativeText(info_text)


def exception_hook(exctype, value, tb):
	ErrorMessage(exctype.__name__, str(value) + '\n' + str(traceback.print_tb(tb))).exec_()