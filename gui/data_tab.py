from PyQt5 import QtWidgets
import os
import serial.tools.list_ports

class DataSourceTab(QtWidgets.QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(12)

        # --- Current Source Label ---
        self.current_source_title = QtWidgets.QLabel("Selected Data Source:")
        self.current_source_value = QtWidgets.QLabel("None")
        self.current_source_value.setWordWrap(True)
        self.current_source_value.setFixedWidth(240)  # Prevents tab from resizing

        source_layout = QtWidgets.QVBoxLayout()
        source_layout.addWidget(self.current_source_title)
        source_layout.addWidget(self.current_source_value)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.layout.addLayout(source_layout)
        self.layout.addWidget(separator)

        # --- LabJack Devices ---
        self.device_group = QtWidgets.QGroupBox("LabJack Devices")
        #self.device_group.setStyleSheet("QGroupBox { margin-top: 6px; margin-bottom: 4px; }")
        lj_layout = QtWidgets.QVBoxLayout(self.device_group)

        self.device_list = QtWidgets.QListWidget()
        self.config_device_button = QtWidgets.QPushButton("Configure Selected Device")
        lj_layout.addWidget(self.device_list)
        lj_layout.addWidget(self.config_device_button)
        self.config_device_button.clicked.connect(self.open_parent_device_config)
        self.layout.addWidget(self.device_group)
        
        self.device_list.addItem("LabJack T7")

        # --- Stream Files ---
        self.stream_group = QtWidgets.QGroupBox("Stream File Inputs")
        stream_layout = QtWidgets.QVBoxLayout(self.stream_group)
        #self.stream_group.setStyleSheet("QGroupBox { margin-top: 6px; margin-bottom: 4px; }")
        self.add_stream_button = QtWidgets.QPushButton("Add Stream File")
        self.stream_list = QtWidgets.QListWidget()
        stream_layout.addWidget(self.add_stream_button)
        stream_layout.addWidget(self.stream_list)

        self.layout.addWidget(self.stream_group)

        # --- Recorded Files ---
        self.recorded_group = QtWidgets.QGroupBox("Recorded File Playback")
        recorded_layout = QtWidgets.QVBoxLayout(self.recorded_group)
        #self.recorded_group.setStyleSheet("QGroupBox { margin-top: 6px; margin-bottom: 4px; }")
        self.load_recorded_button = QtWidgets.QPushButton("Load Recorded File")
        self.recorded_file_label = QtWidgets.QLabel("No file selected.")
        recorded_layout.addWidget(self.load_recorded_button)
        recorded_layout.addWidget(self.recorded_file_label)
        # --- Serial Ports ---
        self.serial_group = QtWidgets.QGroupBox("Serial Ports")
        serial_layout = QtWidgets.QVBoxLayout(self.serial_group)

        self.serial_list = QtWidgets.QListWidget()
        self.refresh_serial_button = QtWidgets.QPushButton("Refresh Serial Ports")
        self.configure_serial_button = QtWidgets.QPushButton("Configure Serial Port")
        self.configure_serial_button.clicked.connect(self.open_serial_config_dialog)

        serial_layout.addWidget(self.serial_list)
        serial_layout.addWidget(self.refresh_serial_button)
        serial_layout.addWidget(self.configure_serial_button)

        self.layout.addWidget(self.serial_group)

        # Connect
        self.refresh_serial_button.clicked.connect(self.refresh_serial_ports)
        
        self.layout.addWidget(self.recorded_group)
        
        # --- Spacer at bottom ---
        self.layout.addStretch(1)
        self.temp_order_button = QtWidgets.QPushButton("Set Temperature Order")
        self.layout.addWidget(self.temp_order_button)
        self.temp_order_button.clicked.connect(self.open_temp_order_overlay)
        
        self.device_list.setFixedWidth(250)
        self.serial_list.setFixedWidth(250)
        self.stream_list.setFixedWidth(250)
        
        self.device_list.setWordWrap(False)
        self.serial_list.setWordWrap(False)
        self.stream_list.setWordWrap(False)
        
        # Connect actions
        self.add_stream_button.clicked.connect(self.add_stream_file)
        self.load_recorded_button.clicked.connect(self.load_recorded_file)
        
        self.selected_source_type = None
        self.selected_source_value = None
        self.recored_file_path = None
        
        self.device_list.itemClicked.connect(lambda item: self.set_current_source("Device", item.text()))
        self.serial_list.itemClicked.connect(lambda item: self.set_current_source("Serial", item.text()))
        self.stream_list.itemClicked.connect(lambda item: self.set_current_source("Stream", item.text()))
        
        self.config_device_button.setEnabled(False)
        self.temp_order_button.setEnabled(False)
        self.configure_serial_button.setEnabled(False)

    
    def refresh_serial_ports(self):
        
        self.serial_list.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.serial_list.addItem(port.device)
    
    def add_stream_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Stream File", "", "All Files (*)")
        if path:
            self.stream_list.addItem(path)
            

    def load_recorded_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Recorded File", "", "CSV/TXT (*.csv *.txt)")
        if path:
            self.recored_file_path = path
            self.recorded_file_label.setText(os.path.basename(path))
            self.set_current_source("Playback", os.path.basename(path))

    def open_parent_device_config(self):
        if self.main_window and hasattr(self.main_window, "open_device_config"):
            self.main_window.open_device_config()
            
    def open_temp_order_overlay(self):
        if hasattr(self.main_window, "open_temp_order_overlay"):
            self.main_window.open_temp_order_overlay()
    
    def open_serial_config_dialog(self):
        if hasattr(self.main_window, "open_serial_config_dialog"):
            self.main_window.open_serial_config_dialog()
    
    def set_current_source(self, source_type, value):
        if source_type != "Serial":
            self.configure_serial_button.setEnabled(False)
        else:
            self.configure_serial_button.setEnabled(True)
            
        if source_type != "Device":
            self.config_device_button.setEnabled(False)
            self.temp_order_button.setEnabled(True)
        else:
            self.config_device_button.setEnabled(True)
            self.temp_order_button.setEnabled(False)
        self.selected_source_type = source_type
        self.selected_source_value = value
        self.current_source_value.setText(f"{source_type}: {value}")
    
    def get_data_source(self):
        source = {"type": self.selected_source_type, "value": self.selected_source_value}
        return source
    
    def clear_inputs(self):
        self.selected_source_type = None
        self.selected_source_value = None
        self.recored_file_path = None
        self.current_source_value.setText(None)
        self.serial_list.clear()
        self.stream_list.clear()
        self.recorded_file_label.setText(None)
    
    def get_serial_sources(self):
        ser_sources = []
        
        for i in range(self.serial_list.count()):
            item = self.serial_list.item(i)
            ser_sources.append(item.text())
        return ser_sources
    
    def get_stream_sources(self):
        stream_sources = []
        
        for i in range(self.stream_list.count()):
            item = self.stream_list.item(i)
            stream_sources.append(item.text())
        return stream_sources
    
    def get_data_sources(self):
        sources = {
            "Serial": self.get_serial_sources(),
            "Stream": self.get_stream_sources(),
            "Playback": self.recored_file_path,
            "Active": self.get_data_source()
        }
        return sources
    
    def load_data_sources(self, config:dict):
        self.clear_inputs()
        serial_sources = config.get("Serial", [])
        stream_sources = config.get("Stream", [])
        self.recored_file_path = config.get("Playback", None)
        if self.recored_file_path is not None:
            self.recorded_file_label.setText(os.path.basename(self.recored_file_path))
        for src in serial_sources:
            self.serial_list.addItem(src)
        for src in stream_sources:
            self.stream_list.addItem(src)
        active = config.get("Active", None)
        if active is not None:
            self.set_current_source(active["type"], active["value"])
        
        
        