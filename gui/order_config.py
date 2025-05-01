from PyQt5 import QtWidgets, QtCore

class TempOrderOverlay(QtWidgets.QWidget):
    def __init__(self, sensor_names, parent=None, config=None):
        super().__init__(parent)
        
        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.SubWindow)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setGeometry(parent.rect())

        self.overlay_layout = QtWidgets.QVBoxLayout(self)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 120);
            }
        """)

        self.card = QtWidgets.QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 6px;
            }
            QGroupBox {
                border: 1px solid palette(dark);
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
            }
        """)
        self.card_layout = QtWidgets.QVBoxLayout(self.card)

        # Grid layout for sensor boxes
        self.grid = QtWidgets.QGridLayout()
        self.sensor_dropdowns = {}

        for i, name in enumerate(sensor_names):
            groupbox = QtWidgets.QGroupBox()
            groupbox_layout = QtWidgets.QVBoxLayout()

            label = QtWidgets.QLabel(f"Sensor: {name}")
            label.setWordWrap(True)
            label.setAlignment(QtCore.Qt.AlignCenter)

            dropdown = QtWidgets.QComboBox()
            dropdown.addItems([str(j + 1) for j in range(len(sensor_names))])
            dropdown.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            groupbox_layout.addWidget(label)
            groupbox_layout.addWidget(dropdown)
            groupbox.setLayout(groupbox_layout)
            groupbox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

            self.grid.addWidget(groupbox, i // 3, i % 3)
            
            self.sensor_dropdowns[name] = dropdown

        self.card_layout.addLayout(self.grid)

        # Buttons
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch(1)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.on_save_clicked)
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.close_button)

        self.card_layout.addLayout(self.button_layout)
        self.overlay_layout.addWidget(self.card, alignment=QtCore.Qt.AlignCenter)
        if config is not None:
            self.load_order(config)
        self.hide()
    
    def load_order(self, config):
        """
        config is -> "Sensor Name": idx
        """
        for sensor in config:
            if sensor not in self.sensor_dropdowns:
                continue
            self.sensor_dropdowns[sensor].setCurrentText(str(config[sensor]))
    
    def on_save_clicked(self):
        order = self.get_sensor_order()
        print("Sensor order saved:", order)  # ✅ Replace this with what you need

        # Optionally: pass order back to main window
        if hasattr(self.parent(), "set_sensor_order"):
            self.parent().set_sensor_order(order)

        self.hide()
    
    def get_sensor_order(self):
        order = {}
        for sensor_name, dropdown in self.sensor_dropdowns.items():
            order[sensor_name] = int(dropdown.currentText())
        return order