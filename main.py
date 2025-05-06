import sys
import numpy as np
import pyvista as pv
from PyQt5 import QtWidgets, QtCore
from PyQt5 import QtGui
from pyvistaqt import QtInteractor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import threading
import time
import os
import json
from gui import live_plotter
from gui import plotter_3D
from daq.meas import TemperatureMeas
from gui.meas_config import DeviceConfigOverlay
from gui.data_tab import DataSourceTab
from gui.order_config import TempOrderOverlay
from gui.serial_config import SerialPortConfigDialog
from gui.calibrator import CalibrationWindow
import queue
from data.serial_loader import SerialLoader
from data.stream_loader import StreamLoader

from PyQt5.QtWidgets import QMessageBox

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DontUseNativeMenuBar, False)

def show_error_message(parent, message, title="Configuration Error"):
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

class SensorManager(QtWidgets.QMainWindow):
    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("VizCalor")
        self.resize(1200, 800)
        
        
         # Central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        self.main_layout = QtWidgets.QHBoxLayout(self.central_widget)

        # LEFT SIDE layout
        self.left_layout = QtWidgets.QVBoxLayout()
        self.left_layout.setSpacing(4)
        self.left_layout.setContentsMargins(0, 4, 0, 0)

        # Logo label (scaled nicely)
        self.logo_label = QtWidgets.QLabel()
        self.logo_pixmap = QtGui.QPixmap("res/logo.png")  # PNG with transparency
        self.logo_pixmap = self.logo_pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setFixedSize(self.logo_pixmap.size())

        # View Control (Buttons)
        self.view_button_3d = QtWidgets.QPushButton("3D View")
        self.view_button_plot = QtWidgets.QPushButton("Plot View")
        self.view_button_3d.setCheckable(True)
        self.view_button_plot.setCheckable(True)
        self.view_button_3d.setChecked(True)

        # Button layout (centered independently)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.view_button_3d)
        self.button_layout.addWidget(self.view_button_plot)
        self.button_layout.addStretch(1)

        self.button_wrapper = QtWidgets.QWidget()
        self.button_wrapper.setLayout(self.button_layout)

        # Top bar layout: logo + centered buttons
        self.top_bar_layout = QtWidgets.QHBoxLayout()
        self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.top_bar_layout.setSpacing(10)
        self.top_bar_layout.addWidget(self.logo_label)
        self.top_bar_layout.addWidget(self.button_wrapper, stretch=1)

        # View Stack
        self.view_stack = QtWidgets.QStackedWidget()
        self.view_stack.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.plotter = QtInteractor(self)
        self.view_stack.addWidget(self.plotter.interactor)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.view_stack.addWidget(self.canvas)

        # Assemble full left layout
        self.left_layout.addLayout(self.top_bar_layout)
        self.left_layout.addWidget(self.view_stack)

        # Add left and right to main layout
        #self.main_layout.addLayout(self.left_layout, stretch=3)
        #self.main_layout.addLayout(self.right_layout, stretch=1)
        self.view_button_3d.clicked.connect(self.switch_to_3d_view)
        self.view_button_plot.clicked.connect(self.switch_to_plot_view)

        # RIGHT SIDE layout
        self.right_layout = QtWidgets.QVBoxLayout()
        self.tabs = QtWidgets.QTabWidget()
        self.right_layout.addWidget(self.tabs)

        # Model Settings Tab
        self.model_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.model_tab, "Model")
        self.model_layout = QtWidgets.QVBoxLayout(self.model_tab)

        self.load_model_button = QtWidgets.QPushButton("Load Model")
        self.model_layout.addWidget(self.load_model_button)

        self.sensor_list = QtWidgets.QListWidget()
        self.model_layout.addWidget(self.sensor_list)

        self.rename_input = QtWidgets.QLineEdit()
        self.model_layout.addWidget(self.rename_input)

        self.rename_button = QtWidgets.QPushButton("Rename Selected")
        self.delete_button = QtWidgets.QPushButton("Delete Selected")
        self.start_test_button = QtWidgets.QPushButton("Start Test")
        self.stop_test_button = QtWidgets.QPushButton("Stop Test")

        self.model_layout.addWidget(self.rename_button)
        self.model_layout.addWidget(self.delete_button)
        self.model_layout.addWidget(self.start_test_button)
        self.model_layout.addWidget(self.stop_test_button)
        self.stop_test_button.setEnabled(False)

        self.device_config_overlay = DeviceConfigOverlay(self)
        self.data_source_tab = DataSourceTab(main_window=self)
        self.temp_order_overlay = None  # Will be created when needed
        self.tabs.addTab(self.data_source_tab, "Data Source")
        # Menu Bar
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.new_project_action = QtWidgets.QAction("New Project", self)
        self.load_project_action = QtWidgets.QAction("Load Project", self)
        self.save_project_action = QtWidgets.QAction("Save Project", self)
        self.file_menu.addAction(self.new_project_action)
        self.file_menu.addAction(self.load_project_action)
        self.file_menu.addAction(self.save_project_action)

        self.new_project_action.triggered.connect(self.new_project)
        self.load_project_action.triggered.connect(self.load_project)
        self.save_project_action.triggered.connect(self.save_project)
        
        self.device_menu = self.menu.addMenu("Device")
        self.add_sensor_type_action = QtWidgets.QAction("Add Sensor", self)
        self.device_menu.addAction(self.add_sensor_type_action)
        self.add_sensor_type_action.triggered.connect(self.device_config_overlay.load_calibration)
        
        self.calib_menu = self.menu.addMenu("Calibration")

        # Add "Open Calibrator" action
        self.open_calibrator_action = QtWidgets.QAction("Open Calibrator", self)
        self.calib_menu.addAction(self.open_calibrator_action)

        # Connect it
        self.open_calibrator_action.triggered.connect(self.open_calibration_tool)
        
         # Connect buttons
        self.load_model_button.clicked.connect(self.load_model)
        self.rename_button.clicked.connect(self.rename_sensor)
        self.delete_button.clicked.connect(self.delete_sensor)
        self.start_test_button.clicked.connect(self.start_test)
        self.stop_test_button.clicked.connect(self.stop_test)
        #
        
        # Final assembly
        self.main_layout.addLayout(self.left_layout, stretch=3)
        self.main_layout.addLayout(self.right_layout, stretch=1)

        # Sensors storage
        self.sensors = []
        self.mesh = None
        self.model_path = None
        self.calibrations = {}

        self.running = False
        self.update_thread = None
        self.refresh_interval = 1.0
        
        self.plot_times = []
        self.view_button_plot.setEnabled(False)
        
        self.project = dict()
        self.project["serial_config"] = None
        self.project["sensor_order"] = None
        
    def update_project_dict(self):
        self.project["meas_config"] = self.device_config_overlay.get_meas_config()
        self.project["model_path"] = self.model_path
        self.project["sensors"] = [{"position": point.tolist(), "name": name} for point, cube_actor, label_actor, name in self.sensors]
        #print("project sensors: ", self.project["sensors"])
        #self.project["serial_config"] = dict() # -> this gets saved every time its changed
        self.project["data_source"] = self.data_source_tab.get_data_sources()
    
    def open_calibration_tool(self):
        if not hasattr(self, 'calibration_window'):
            self.calibration_window = CalibrationWindow()
        self.calibration_window.show()
        self.calibration_window.raise_()
        self.calibration_window.activateWindow()

    def open_device_config(self):
        self.device_config_overlay.show()
        
    def save_device_config(self, config):
        #print("Save config: ", config)
        self.project["meas_config"] = config
    
    def open_temp_order_overlay(self):
        
        sensor_names = [s[3] for s in self.sensors]  # assuming sensors are (pos, id, actor, name)
        if self.temp_order_overlay:
            self.temp_order_overlay.close()
        self.temp_order_overlay = TempOrderOverlay(sensor_names, parent=self, config=self.project["sensor_order"])
        self.temp_order_overlay.show()
    
    def set_sensor_order(self, order: dict):
        self.project["sensor_order"] = order
        #print("Updated sensor order:", order)
    
    def switch_to_3d_view(self):
        self.view_stack.setCurrentIndex(0)
        self.view_button_3d.setChecked(True)
        self.view_button_plot.setChecked(False)

    def switch_to_plot_view(self):
        self.view_stack.setCurrentIndex(1)
        self.view_button_plot.setChecked(True)
        self.view_button_3d.setChecked(False)
    
    def switch_view_tab(self, index):
        self.view_stack.setCurrentIndex(index)
        
    def open_serial_config_dialog(self):
        dialog = SerialPortConfigDialog(self, config=self.project["serial_config"])
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            config = dialog.get_config()
            self.project["serial_config"] = config
    
    def clear_project(self):
        self.plotter.clear()
        self.sensors.clear()
        self.sensor_list.clear()
        self.model_path = None
        
        self.device_config_overlay.clear_inputs()
        self.data_source_tab.clear_inputs()
        self.project["serial_config"] = None
        self.project["sensor_order"] = None
        self.update_project_dict()
    
    def new_project(self):
        if self.sensors or self.model_path:
            reply = QtWidgets.QMessageBox.question(self, 'Save Project?', 'Do you want to save the current project?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Yes:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return

        self.clear_project()
        


    def save_project(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.vizcalor)")
        if not fileName:
            return
        self.update_project_dict()
        with open(fileName, 'w') as f:
            json.dump(self.project, f, indent=4)

    def load_sensors(self, sensors:dict):
        for sensor in sensors:
            #print("sensor:", sensor)
            position = np.array(sensor["position"])
            name = sensor["name"]
            cube = pv.Cube(center=position, x_length=0.05, y_length=0.05, z_length=0.05)
            cube_actor = self.plotter.add_mesh(cube, style='wireframe', color='red')
            label_actor = self.plotter.add_point_labels(position, [name], font_size=12, text_color='white')
            self.plotter.disable_picking()
            self.plotter.enable_surface_point_picking(callback=self.add_sensor, show_point=False)
            self.sensors.append((position, cube_actor, label_actor, name))
            self.sensor_list.addItem(name)
            
    def load_project(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Project", "", "Project Files (*.vizcalor)")
        if not fileName or fileName == "":
            return
        
        try:
            with open(fileName, 'r') as f:
                project = json.load(f)
                
            self.new_project()
            
            self.model_path = project.get("model_path", None)
            
            if self.model_path and os.path.exists(self.model_path):
                self.plotter.clear()
                self.mesh = pv.read(self.model_path)
                self.surface = self.mesh.extract_surface()
                self.plotter.add_mesh(self.surface, show_edges=True)  # Just show the model
                self.project["model_path"] = self.model_path
            else:
                show_error_message(self, "Invalid Path to 3D model.\n Model was either deleted or moved!", "Load Error")
                self.clear_project()
                return
            #print("Model loaded")
            self.load_sensors(project.get("sensors", []))
        
            #print("sensors loaded")
            
            meas_config = project.get("meas_config", dict())
            
            sensor_names = [sensor[3] for sensor in self.sensors]
            self.device_config_overlay.load_config(meas_config, sensor_names)
            #print("Meas config loaded")
            self.project["serial_config"] = project.get("serial_config", None)
            self.project["sensor_order"] = project.get("sensor_order", None)
            self.data_source_tab.load_data_sources(project.get("data_source", {}))
            self.update_project_dict()
            #print("print: Done")

        except Exception as e:
            self.clear_project()
            print(e)
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load project: {e}")


    def load_model(self):
        options = QtWidgets.QFileDialog.Options()
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open 3D Model", "", "3D Files (*.stl *.obj *.ply)", options=options)
        if fileName:
            try:
                self.plotter.clear()
                self.mesh = pv.read(fileName)
                self.surface = self.mesh.extract_surface()
                self.plotter.add_mesh(self.surface, show_edges=True)
                self.plotter.enable_surface_point_picking(callback=self.add_sensor, show_point=False)
                self.model_path = fileName
            except Exception as e:
                print(f"Error loading model: {e}")

    def add_sensor(self, picked_point):
        if self.mesh is None:
            return

        picker = self.plotter.iren.interactor.GetPicker()
        cell_id = picker.GetCellId()
        if cell_id < 0:
            return

        cell = self.surface.extract_cells(cell_id)
        points = cell.points
        if len(points) != 3:
            return

        A, B, C = points
        AB = B - A
        AC = C - A
        normal = np.cross(AB, AC)
        normal = normal / np.linalg.norm(normal)

        vec = picked_point - A
        distance = np.dot(vec, normal)
        projected_point = picked_point - distance * normal

        cube = pv.Cube(center=projected_point, x_length=0.05, y_length=0.05, z_length=0.05)
        cube_actor = self.plotter.add_mesh(cube, style='wireframe', color='red')

        sensor_name = f"Sensor {len(self.sensors)}"
        label_actor = self.plotter.add_point_labels(projected_point, [sensor_name], font_size=12, text_color='white')

        self.sensors.append((projected_point, cube_actor, label_actor, sensor_name))
        self.sensor_list.addItem(sensor_name)
        sensor_names = [sensor[3] for sensor in self.sensors]
        self.device_config_overlay.update_ain_sensor_list(sensor_names)

    def rename_sensor(self):
        selected_items = self.sensor_list.selectedItems()
        if not selected_items:
            return

        new_name = self.rename_input.text().strip()
        """
        if not new_number.isdigit():
            return
        """
        
        new_name = new_name #f"Sensor {new_number}"
        selected_row = self.sensor_list.currentRow()
        point, cube_actor, label_actor, _ = self.sensors[selected_row]

        self.plotter.remove_actor(label_actor)

        new_label_actor = self.plotter.add_point_labels(point, [new_name], font_size=12, text_color='white')

        self.sensors[selected_row] = (point, cube_actor, new_label_actor, new_name)

        self.sensor_list.item(selected_row).setText(new_name)
        self.rename_input.clear()
        sensor_names = [sensor[3] for sensor in self.sensors]
        self.device_config_overlay.update_ain_sensor_list(sensor_names)

    def delete_sensor(self):
        selected_items = self.sensor_list.selectedItems()
        if not selected_items:
            return

        selected_row = self.sensor_list.currentRow()

        point, cube_actor, label_actor, name = self.sensors.pop(selected_row)
        try:
            self.plotter.remove_actor(cube_actor)
            self.plotter.remove_actor(label_actor)
        except Exception as e:
            print(f"Warning: failed to remove actor: {e}")

        self.sensor_list.takeItem(selected_row)
        sensor_names = [sensor[3] for sensor in self.sensors]
        self.device_config_overlay.update_ain_sensor_list(sensor_names)
        self.plotter.render()
        
    def disable_gui(self):
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.rename_input.setEnabled(False)
        self.sensor_list.setEnabled(False)
        
        self.start_test_button.setEnabled(False)
        self.load_model_button.setEnabled(False)
        self.view_button_plot.setEnabled(True)
        self.stop_test_button.setEnabled(True)
        
    def enable_gui(self): 
        self.rename_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.rename_input.setEnabled(True)
        self.sensor_list.setEnabled(True)

        self.start_test_button.setEnabled(True)
        self.load_model_button.setEnabled(True)
        self.view_button_plot.setEnabled(False)
        self.stop_test_button.setEnabled(False)
        
    def start_test(self):
        QtCore.QTimer.singleShot(100, self._start_test_internal)
    
    def channel_map(self):
        pass
    
    def _prepare_data_source(self):
        """
        Prepares loader for selected data source
        """
        source = self.data_source_tab.get_data_source()
        print("source: ", source)
        if source["type"] == None:
            show_error_message(self, "No Data Source Selected", "Configuration Error")
            return False
        
        if source["type"] == "Device":
            # prepare LabJack reader
            errors = self.device_config_overlay.varify_valid_setup()
            if len(errors) > 0:
                show_error_message(self, errors[0], "Configuration Error")
                return False
            channels = self.device_config_overlay.get_active_channels()
            meas_config = self.device_config_overlay.get_meas_config()
            self.data_source = TemperatureMeas(channels, meas_config, self.meas_q)
        elif source["type"] == "Serial":
            if self.project["serial_config"] is None:
                show_error_message(self, "Serial Port Not Configured")
                return False
            self.data_source = SerialLoader(source["value"], self.project["serial_config"], self.meas_q)
        elif source["type"] == "Stream":
            self.data_source = StreamLoader(source["value"], self.meas_q)
        else:
            show_error_message(self, f"Data source - {source['type']}: Not yet implemented")
            return False
        return True
    
    def _start_test_internal(self):

        
        if self.mesh is None:
            show_error_message(self, "No 3D model Loaded")
            return
        
        self.meas_q = queue.Queue()
        if not self._prepare_data_source():
            # some error 
            return
        
        self.plotter.clear()
        self.disable_gui()    
        
        self.sensor_positions = np.array([point for point, _, _, _ in self.sensors])        
        self.num_sensors = self.sensor_positions.shape[0]
        self.temperatures = np.random.uniform(20, 25, self.num_sensors)
        
        
        labels = [s[3] for s in self.sensors]
        self.live_plotter = live_plotter.LivePlotter(self.figure, self.canvas, labels)
        self.plotter_3D = plotter_3D.Plotter3D(self.plotter, self.mesh, self.sensor_positions, labels)
        
        #self.refresh_interval = 1.0 / self.refresh_slider.value()
        # Update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_temperatures_loop)
        self.update_thread.start()
        
        
        self.data_source.start()
        
        
    def stop_test(self):
        self.running = False
        if self.update_thread is not None:
            self.update_thread.join()
            
        if self.data_source is not None:
            self.data_source.stop() # TODO: Unblock the update thread somehow
            
        self.plotter.clear()

        if self.mesh is not None:
            self.plotter_3D.reset()
            
            for point, cube_actor, label_actor, name in self.sensors:
                cube = pv.Cube(center=point, x_length=0.05, y_length=0.05, z_length=0.05)
                self.plotter.add_mesh(cube, style='wireframe', color='red')
                self.plotter.add_point_labels(point, [name], font_size=12, text_color='white')
            self.plotter.disable_picking()
            self.plotter.enable_surface_point_picking(callback=self.add_sensor, show_point=False)

        self.enable_gui()
        

    def update_temperatures_loop(self):
        while self.running:
            
            #self.plotter.iren.interrupt()
            #self.temperatures += np.random.uniform(-3, 3, self.num_sensors)
            #self.temperatures = np.clip(self.temperatures, 20, 80)
            temps = self.meas_q.get()
            self.plotter_3D.update_temperatures(temps)
            self.live_plotter.update(temps)
            #time.sleep(self.refresh_interval)
    

    def closeEvent(self, event):
        self.running = False
        if self.update_thread is not None:
            self.update_thread.join()
        if self.plotter is not None:
            self.plotter.close()
        QtWidgets.QApplication.quit()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("res/logo.png"))
    app.setApplicationName("VizCalor")
    app.setOrganizationName("SimonPechacek")
    window = SensorManager()
    window.show()
    sys.exit(app.exec_())
