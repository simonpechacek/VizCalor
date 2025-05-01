import numpy as np
import pyvista as pv
from scipy.interpolate import Rbf

class Plotter3D(object):
    def __init__(self, plotter, mesh, sensor_positions, labels):
        self.plotter = plotter
        self.mesh = mesh
        self.sensor_positions = sensor_positions
        
        self.plotter.clear()
        
        self.surface = self.mesh.extract_surface()
        
        self.num_sensors = self.sensor_positions.shape[0]
        self.points = self.surface.points
        
        # first init -> random
        initial_temperatures = np.random.uniform(20, 25, self.num_sensors)
        self.mesh['Temperature'] = self.interpolate_temperatures(initial_temperatures)
        
        self.mesh_actor = self.plotter.add_mesh(self.mesh, scalars='Temperature', cmap='plasma', show_edges=True, interpolate_before_map=True)
        #self.plotter.add_points(self.sensor_positions, color='black', point_size=25, render_points_as_spheres=True)
        self.plotter.add_point_labels(
            self.sensor_positions,
            labels,
            point_size=25,
            font_size=12,
            text_color='white'
        )

        
        
    def interpolate_temperatures(self, temperatures):
        rbf = Rbf(self.sensor_positions[:, 0], self.sensor_positions[:, 1], self.sensor_positions[:, 2], temperatures, function='multiquadric')
        return rbf(self.points[:, 0], self.points[:, 1], self.points[:, 2])
    
    def update_temperatures(self, temperatures):
        self.mesh['Temperature'] = self.interpolate_temperatures(temperatures)
        self.mesh_actor.GetMapper().SetScalarRange(15, 30)
        self.mesh_actor.GetMapper().Modified()
        self.plotter.render()
        
    def reset(self):
        """
        resets to original mesh
        """
        self.plotter.clear()
        # Clear the temperatures from before
        if self.mesh is not None:
            if 'Temperature' in self.mesh.point_data:
                del self.mesh.point_data['Temperature']
        
        self.plotter.add_mesh(self.mesh, show_edges=True)
        
