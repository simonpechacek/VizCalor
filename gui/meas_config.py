from PyQt5 import QtWidgets, QtCore
import os
import json

class DeviceConfigOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.SubWindow )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #self.setWindowModality(QtCore.Qt.ApplicationModal)  # Block input to main window
        self.setFixedSize(parent.size())
        
        self.overlay_layout = QtWidgets.QVBoxLayout(self)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        # Add dimming background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 120);  /* semi-transparent black */
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
        self.overlay_layout.addWidget(self.card, alignment=QtCore.Qt.AlignHCenter)
        # --- AIN Configuration Area (3 columns) ---
        self.ain_scroll = QtWidgets.QScrollArea()
        self.ain_scroll.setWidgetResizable(True)
        self.ain_widget = QtWidgets.QWidget()
        self.ain_grid = QtWidgets.QGridLayout(self.ain_widget)

        self.ain_controls = []
        for i in range(14):
            groupbox = QtWidgets.QGroupBox(f"AIN {i}")
            vbox = QtWidgets.QVBoxLayout()
            checkbox = QtWidgets.QCheckBox("Enable")
            
            combo = QtWidgets.QComboBox()
            combo.addItem("Select Sensor")
            calibration_combo = QtWidgets.QComboBox()
            calibration_combo.addItem("Select Calibration")
            vbox.addWidget(checkbox)
            vbox.addWidget(combo)
            vbox.addWidget(calibration_combo)
            groupbox.setLayout(vbox)
            
            def make_toggle_handler(sensor_cb, calib_cb):
                return lambda state: (
                    sensor_cb.setEnabled(state == QtCore.Qt.Checked),
                    calib_cb.setEnabled(state == QtCore.Qt.Checked)
                )

            checkbox.setChecked(False)
            combo.setEnabled(False)
            calibration_combo.setEnabled(False)
            checkbox.stateChanged.connect(make_toggle_handler(combo, calibration_combo))
            self.ain_grid.addWidget(groupbox, i // 3, i % 3)
            self.ain_controls.append((checkbox, combo, calibration_combo))

        self.ain_scroll.setWidget(self.ain_widget)
        self.ain_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # --- Calibration Area ---
        self.calibration_layout = QtWidgets.QVBoxLayout()
        self.calibration_label = QtWidgets.QLabel("Calibrations")
        self.calibration_list = QtWidgets.QListWidget()
        self.load_calibration_button = QtWidgets.QPushButton("Load Calibration")
        self.delete_calibration_button = QtWidgets.QPushButton("Delete Selected Calibration")
        self.calibration_layout.addWidget(self.calibration_label)
        self.calibration_layout.addWidget(self.load_calibration_button)
        self.calibration_layout.addWidget(self.calibration_list)
        self.calibration_layout.addWidget(self.delete_calibration_button)

        # --- Split AIN and Calibration ---
        self.top_split = QtWidgets.QHBoxLayout()
        self.top_split.addWidget(self.ain_scroll, stretch=3)
        self.top_split.addLayout(self.calibration_layout, stretch=1)
        self.card_layout.addLayout(self.top_split)

        # --- SINGLE ROW: Resolution, Refresh, Settling ---
        self.lower_left_layout = QtWidgets.QHBoxLayout()

        # --- Resolution block ---
        res_group = QtWidgets.QVBoxLayout()
        self.resolution_label = QtWidgets.QLabel("Resolution: Auto")
        self.resolution_label.setAlignment(QtCore.Qt.AlignCenter)
        self.resolution_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.resolution_slider.setMinimum(0)
        self.resolution_slider.setMaximum(8)
        self.resolution_slider.setValue(0)
        self.resolution_slider.setFixedWidth(150)
        res_group.addWidget(self.resolution_label)
        res_group.addWidget(self.resolution_slider)

        # --- Refresh block ---
        refresh_group = QtWidgets.QVBoxLayout()
        self.refresh_label = QtWidgets.QLabel("Refresh Frequency: 1 Hz")
        self.refresh_label.setAlignment(QtCore.Qt.AlignCenter)
        self.refresh_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.refresh_slider.setMinimum(1)
        self.refresh_slider.setMaximum(10)
        self.refresh_slider.setValue(1)
        self.refresh_slider.setFixedWidth(150)
        refresh_group.addWidget(self.refresh_label)
        refresh_group.addWidget(self.refresh_slider)

        # --- Settling time field ---
        settling_group = QtWidgets.QVBoxLayout()
        settling_label = QtWidgets.QLabel("Settling Time (ms)")
        settling_label.setAlignment(QtCore.Qt.AlignCenter)
        self.settling_time_input = QtWidgets.QLineEdit()
        self.settling_time_input.setPlaceholderText("0-50")
        self.settling_time_input.setMaximumWidth(100)
        self.settling_time_input.setAlignment(QtCore.Qt.AlignCenter)
        settling_group.addWidget(settling_label)
        settling_group.addWidget(self.settling_time_input)

        # --- Combine all 3 groups ---
        self.lower_left_layout.addStretch()
        self.lower_left_layout.addLayout(res_group)
        self.lower_left_layout.addSpacing(20)
        self.lower_left_layout.addLayout(refresh_group)
        self.lower_left_layout.addSpacing(20)
        self.lower_left_layout.addLayout(settling_group)
        self.lower_left_layout.addStretch()
        self.resolution_slider.valueChanged.connect(self.update_resolution_label)
        self.refresh_slider.valueChanged.connect(self.update_refresh_label)
        self.settling_time_input.textChanged.connect(self.recalculate_refresh_rate)
        
        # --- Save & Close buttons ---
        self.save_close_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save")
        self.close_button = QtWidgets.QPushButton("Close")
        self.save_button.clicked.connect(self.save_config)
        self.close_button.clicked.connect(self.hide)
        self.save_close_layout.addStretch(1)
        self.save_close_layout.addWidget(self.save_button)
        self.save_close_layout.addWidget(self.close_button)

        # --- Bottom row (left/right) ---
        self.bottom_row = QtWidgets.QHBoxLayout()
        self.bottom_row.addLayout(self.lower_left_layout, stretch=3)
        self.bottom_row.addLayout(self.save_close_layout, stretch=1)

        self.card_layout.addLayout(self.bottom_row)
        
        self.load_calibration_button.clicked.connect(self.load_calibration)
        
        
        self.calibrations = dict()
        # --- Final overlay ---
        self.overlay_layout.addWidget(self.card)
        self.hide()
    
    def save_config(self):
        config = self.get_meas_config()
        if hasattr(self.parent(), "save_device_config"):
            self.parent().save_device_config(config)
    
    def show(self):
        super().show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
    
    def toggle_ain_inputs(self, state, combo, calibration_combo):
        enabled = (state == QtCore.Qt.Checked)
        combo.setEnabled(enabled)
        calibration_combo.setEnabled(enabled)
        self.recalculate_refresh_rate()
        
    # Functions (new_config, load_config, save_config) will be added here
    def recalculate_refresh_rate(self):
        pass

    def update_resolution_label(self):
        val = self.resolution_slider.value()
        if val == 0:
            text = "Resolution: Auto"
        else:
            text = f"Resolution: {11 + val} bits"
        self.resolution_label.setText(text)

    def update_refresh_label(self):
        value = self.refresh_slider.value()
        self.refresh_label.setText(f"Refresh Frequency: {value} Hz")

    def clear_inputs(self):
        for checkbox, combo, combo_calib in self.ain_controls:
            checkbox.setChecked(False)
            combo.clear()
            combo_calib.clear()
            combo.addItem("Select Sensor")
            combo_calib.addItem("Select Calibration")
            
        self.resolution_slider.setValue(0)
        self.settling_time_input.clear()
        self.refresh_slider.setValue(1)
    
    def load_config(self, config:dict, sensors=[]):
        self.calibrations = config.get("calibrations", {})
        self.update_ain_calibration_list()
        self.update_ain_sensor_list(sensors)
        
        for channel_name, channel in config.get("ain_channels", {}).items():
            try:
                idx = int(channel_name.replace("AIN", ""))
            except Exception as e:
                print(e)
                continue
            #print("Load idx: ", idx, " -> ", channel_name)
            if idx >= len(self.ain_controls):
                continue
            checkbox, combo, combo_calib = self.ain_controls[idx]
            checkbox.setChecked(channel.get("enabled", False))
            assigned = channel.get("assigned_sensor", None)
            assigned_calib = channel.get("assigned_calibration", None)
            if assigned:
                index = combo.findText(assigned)
                if index != -1:
                    combo.setCurrentIndex(index)
            if assigned_calib:
                index = combo_calib.findText(assigned_calib)
                if index != -1:
                    combo_calib.setCurrentIndex(index)

        self.resolution_slider.setValue(config.get("RESOLUTION", 0))
        self.settling_time_input.setText(str(config.get("SETTLING_MS", 0)))
        self.refresh_slider.setValue(config.get("SCAN_FREQ", 1))
        
    def load_calibration(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Calibration", "", "Calibration Files (*.json)")
        try:
            if fileName != "":
                name = os.path.basename(fileName).replace('.json', '')
            else:
                return
            with open(fileName, 'r') as f:
                self.calibrations[name] = json.load(f)
        
            self.calibration_list.addItem(name)
            self.update_ain_calibration_list()
        except FileNotFoundError as e:
            print(e)

    def delete_calibration(self):
        item = self.calibration_list.currentItem()
        if item:
            name = item.text()
        del self.calibrations[name]
        self.calibration_list.takeItem(self.calibration_list.row(item))
        self.update_ain_calibration_list()

    def update_ain_calibration_list(self):
        names = ["Select Calibration"] + list(self.calibrations.keys())
        for checkbox, combo, calibration_combo in self.ain_controls:
            current = calibration_combo.currentText()
            calibration_combo.clear()
            calibration_combo.addItems(names)
            if current in names:
                calibration_combo.setCurrentText(current)
    
    def update_ain_sensor_list(self, sensor_names):
        for checkbox, combo, calibration_combo in self.ain_controls:
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Select Sensor")
            combo.addItems(sensor_names)
            index = combo.findText(current)
            if index != -1:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
    
    def get_meas_config(self):
        config = {
            "ain_channels": dict(),
            "RESOLUTION": self.resolution_slider.value(),
            "SETTLING_MS": int(self.settling_time_input.text()) if self.settling_time_input.text().isdigit() else 0,
            "SCAN_FREQ": self.refresh_slider.value(),
            "calibrations": self.calibrations
        }
        for i, control in enumerate(self.ain_controls):
            checkbox, combo, combo_calib = control
            config["ain_channels"][f"AIN{i}"] = {
                "enabled": checkbox.isChecked(),
                "assigned_sensor": combo.currentText() if combo.currentIndex() != 0 else None,
                "assigned_calibration": combo_calib.currentText() if combo.currentIndex() != 0 else None
            } 
        return config
    
    def get_active_channels(self):
        channels = []
        for idx in range(len(self.ain_controls)):
            checkbox, _,  _ = self.ain_controls[idx]
            if checkbox.isChecked():
                channels.append(f"AIN{idx}")
        return channels
    
    def varify_valid_setup(self):
        errors = []
        selected_sensors = set()
        for i, control in enumerate(self.ain_controls):
            checkbox, combo, combo_calib = control
            if checkbox.isChecked():
                if combo.currentIndex() == 0:
                    errors.append(f"AIN{i} - no sensor assigned")
                else:
                    sensor_assign = combo.currentText()
                    if sensor_assign in selected_sensors:
                        errors.append(f"AIN{i} - uses already assigned sensor")
                    else:
                        selected_sensors.add(sensor_assign)
                if combo_calib.currentIndex() == 0:
                    errors.append(f"AIN{i} - no celibration/type assigned")
                    
        return errors
        
"""
        # Calibrations Tab
        self.calibration_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.calibration_layout = QtWidgets.QVBoxLayout(self.calibration_tab)

        self.load_calibration_button = QtWidgets.QPushButton("Load Calibration")
        self.calibration_layout.addWidget(self.load_calibration_button)

        self.calibration_list = QtWidgets.QListWidget()
        self.calibration_layout.addWidget(self.calibration_list)

        self.delete_calibration_button = QtWidgets.QPushButton("Delete Selected Calibration")
        self.calibration_layout.addWidget(self.delete_calibration_button)

        self.load_calibration_button.clicked.connect(self.load_calibration)
        self.delete_calibration_button.clicked.connect(self.delete_calibration)


"""
        
"""
# Create a widget that will live inside the scroll area
        self.ain_widget = QtWidgets.QWidget()
        self.ain_scroll.setWidget(self.ain_widget)

        # Create a vertical layout for all AIN groupboxes
        self.ain_layout = QtWidgets.QVBoxLayout(self.ain_widget)
        self.ain_layout.setSpacing(5)

        # Fill with AIN groupboxes
        self.ain_controls = []

        for i in range(14):
            groupbox = QtWidgets.QGroupBox(f"AIN {i}")
            vbox = QtWidgets.QVBoxLayout()

            checkbox = QtWidgets.QCheckBox("Enable")
            combo = QtWidgets.QComboBox()
            combo.addItem("Select Sensor")
            calibration_combo = QtWidgets.QComboBox()
            calibration_combo.addItem("Select Calibration")

            vbox.addWidget(checkbox)
            vbox.addWidget(combo)
            vbox.addWidget(calibration_combo)
            groupbox.setLayout(vbox)
            
            self.ain_layout.addWidget(groupbox)

            self.ain_controls.append((checkbox, combo, calibration_combo))

        self.measurement_layout.addWidget(self.ain_scroll)

self.resolution_group = QtWidgets.QGroupBox()
        self.resolution_layout = QtWidgets.QVBoxLayout(self.resolution_group)

        self.resolution_title = QtWidgets.QLabel("Resolution Settings")
        self.resolution_title.setAlignment(QtCore.Qt.AlignCenter)
        self.resolution_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.resolution_slider.setMinimum(0)
        self.resolution_slider.setMaximum(8)
        self.resolution_slider.setValue(0)

        self.resolution_label = QtWidgets.QLabel("Resolution: Auto")
        self.resolution_label.setAlignment(QtCore.Qt.AlignCenter)
        self.settling_time_input = QtWidgets.QLineEdit()
        self.settling_time_input.setPlaceholderText("Settling time (0-50 ms)")
        self.settling_time_input.textChanged.connect(self.recalculate_refresh_rate)

        self.resolution_layout.addWidget(self.resolution_title)
        self.resolution_layout.addWidget(self.resolution_slider)
        self.resolution_layout.addWidget(self.resolution_label)
        self.resolution_layout.addWidget(self.settling_time_input)

        self.measurement_layout.addWidget(self.resolution_group)
        
        # Refresh Frequency slider
        self.refresh_label = QtWidgets.QLabel("Refresh Frequency: 1 Hz")
        self.refresh_label.setAlignment(QtCore.Qt.AlignCenter)
        self.refresh_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.refresh_slider.setMinimum(1)
        self.refresh_slider.setMaximum(10)
        self.refresh_slider.setValue(1)
        self.measurement_layout.addWidget(self.refresh_label)
        self.measurement_layout.addWidget(self.refresh_slider)

"""