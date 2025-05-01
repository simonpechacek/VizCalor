from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import pandas as pd
import os
import json

def show_error_message(parent, message, title="Configuration Error"):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

class CalibrationWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calibration Tool")
        self.resize(1000, 600)

        main_layout = QtWidgets.QHBoxLayout(self)

        # --- Plot Area (2/3 width) ---
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumWidth(int(self.width() * 2 / 3))
        
        main_layout.addWidget(self.canvas)

        # --- Controls Panel (1/3 width) ---
        self.controls = QtWidgets.QVBoxLayout()
        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("res/logo.png")  # Replace with your actual path
        pixmap = pixmap.scaledToHeight(128, QtCore.Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(QtCore.Qt.AlignCenter)
        # 1) Load Data button
        self.load_data_button = QtWidgets.QPushButton("Load Data")
        self.controls.addWidget(self.load_data_button)

        # 2) Polynomial order selector
        self.poly_label = QtWidgets.QLabel("Select Polynomial Order:")
        self.poly_order = QtWidgets.QComboBox()
        self.poly_order.addItems([str(i) for i in range(11)])
        self.controls.addWidget(self.poly_label)
        self.controls.addWidget(self.poly_order)

        # 3) Calculate button
        self.calc_button = QtWidgets.QPushButton("Calculate Calibration")
        self.controls.addWidget(self.calc_button)
        self.calc_button.clicked.connect(self.calc_calibration)
        # 4) Save calibration button
        self.save_button = QtWidgets.QPushButton("Save Calibration")
        self.controls.addWidget(self.save_button)

        # Spacer to push widgets to the top
        self.controls.addStretch()
        control_widget = QtWidgets.QWidget()
        control_widget.setLayout(self.controls)
        control_widget.setMaximumWidth(300)

        main_layout.addWidget(control_widget)
        self.controls.insertWidget(0, logo)
        # Connect actions (optional)
        self.save_button.clicked.connect(self.save_calibration)
        self.load_data_button.clicked.connect(self.load_data)
        
        self.voltages = None
        self.temps = None
        self.coeffs = None
        self.prepare_plot()
        self.canvas.draw()

    def prepare_plot(self):
        self.ax = self.figure.add_subplot(111)
        self.figure.patch.set_facecolor('#1e1e1e')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.set_xlabel('Voltage (V)', color='white')
        self.ax.set_ylabel('Temperature (°C)', color='white')
        self.ax.set_axisbelow(True)
        self.ax.grid(True, color='white', alpha=0.2)
        
    
    def parse_calibration_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            df = pd.read_csv(file_path)
            if "Voltage" not in df.columns or "Temperature" not in df.columns:
                raise ValueError("CSV must contain 'Voltage' and 'Temperature' columns.")
            voltages = df["Voltage"].to_numpy()
            temperatures = df["Temperature"].to_numpy()

        elif ext == ".txt":
            data = np.loadtxt(file_path)
            if data.shape[1] != 2:
                raise ValueError("TXT file must have exactly 2 columns: voltage and temperature.")
            voltages = data[:, 0]
            temperatures = data[:, 1]

        elif ext == ".npy":
            data = np.load(file_path)
            if data.ndim != 2 or data.shape[1] != 2:
                raise ValueError("NPY file must contain a 2D array with 2 columns.")
            voltages = data[:, 0]
            temperatures = data[:, 1]

        else:
            show_error_message(self, "Invalid Data format", "Data Load Error")
            return None, None

        return voltages, temperatures
        
    def plot_data(self):
        #self.prepare_plot()
        for artist in self.ax.lines + self.ax.collections:
            artist.remove()
        self.ax.scatter(self.voltages, self.temps, c='#88b04b')
        self.canvas.draw()
        
    def load_data(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                                                        self,
                                                        "Load Data",
                                                        "",
                                                        "Supported Files (*.csv *.txt *.npy);;All Files (*)"
                                                    )
        if file_path and file_path != "":
            #print("Data file selected:", file_path)
            # Load and parse the CSV here
            try:
                voltges, temps = self.parse_calibration_file(file_path)
                if voltges is not None:
                    self.voltages = voltges
                    self.temps = temps
                    self.plot_data()
            except Exception as e:
                show_error_message(self, str(e), "Load Error")
        

    def calc_calibration(self):
        if self.voltages is None:
            show_error_message(self, "No data Loaded!", "Data Error")
            return
        order = int(self.poly_order.currentText())
        coeffs = np.polyfit(self.voltages, self.temps, order)
        def func(voltage):
            res = 0
            for i in range(len(coeffs)):
                res += coeffs[i] * (voltage**(order - i))
            return res
        fit_data = list(map(func, self.voltages))
        
        #self.prepare_plot()
        for artist in self.ax.lines + self.ax.collections:
            artist.remove()
        self.ax.scatter(self.voltages, self.temps, c='#88b04b')
        self.ax.plot(self.voltages, fit_data, c='#92a8d1')
        self.coeffs = coeffs
        self.canvas.draw()
        
    
    def save_calibration(self):
        if self.coeffs is None:
            show_error_message(self, "Calibration not calculated! Nothing to save!", "Data Missing Error")
            return
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Calibration", "", "JSON Files (*.json);;All Files (*)")
        if file_path and file_path != "":
            #print("Save to:", file_path)
            # Save the calibration parameters here
            calib = {"T_FUNC":  list(self.coeffs)}
            with open(file_path, "w") as f:
                json.dump(calib, f)
            
