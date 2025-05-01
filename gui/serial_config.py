from PyQt5 import QtWidgets, QtGui

class SerialPortConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Serial Port Configuration")
        self.setModal(True)
        self.setFixedWidth(300)

        layout = QtWidgets.QFormLayout(self)

        # Baudrate
        self.baudrate_input = QtWidgets.QLineEdit()
        self.baudrate_input.setPlaceholderText("115200")
        self.baudrate_input.setValidator(QtGui.QIntValidator(1, 10000000))
        layout.addRow("Baudrate:", self.baudrate_input)

        # Bytesize
        self.bytesize_combo = QtWidgets.QComboBox()
        self.bytesize_combo.addItems(["FIVEBITS", "SIXBITS", "SEVENBITS", "EIGHTBITS"])
        self.bytesize_combo.setCurrentText("EIGHTBITS")
        layout.addRow("Byte Size:", self.bytesize_combo)

        # Parity
        self.parity_combo = QtWidgets.QComboBox()
        self.parity_combo.addItems(["NONE", "EVEN", "ODD", "MARK", "SPACE"])
        self.parity_combo.setCurrentText("NONE")
        layout.addRow("Parity:", self.parity_combo)

        # Stopbits
        self.stopbits_combo = QtWidgets.QComboBox()
        self.stopbits_combo.addItems(["ONE", "TWO", "ONE_POINT_FIVE"])
        self.stopbits_combo.setCurrentText("ONE")
        layout.addRow("Stop Bits:", self.stopbits_combo)

        # Save and Cancel buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addRow(btn_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)
        if config is not None:
            self.load_config(config)
            
    def load_config(self, config):
        self.baudrate_input.setText(str(config.get("baudrate", "")))
        self.bytesize_combo.setCurrentText(config.get("bytesize", "EIGHTBITS"))
        self.parity_combo.setCurrentText(config.get("parity", "NONE"))
        self.stopbits_combo.setCurrentText(config.get("stopbits", "ONE"))
    
    def get_config(self):
        return {
            "baudrate": int(self.baudrate_input.text()) if self.baudrate_input.text() else 115200,
            "bytesize": self.bytesize_combo.currentText(),
            "parity": self.parity_combo.currentText(),
            "stopbits": self.stopbits_combo.currentText()
        }