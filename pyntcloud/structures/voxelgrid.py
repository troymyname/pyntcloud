#  HAKUNA MATATA

"""
VoxelGrid Class
"""

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.spatial import cKDTree

from ..plot import plot_voxelgrid
from ..utils.array import cartesian


class VoxelGrid(object):
    
    def __init__(self, points, x_y_z=[2, 2, 2], bb_cuboid=True):
        """
        Parameters
        ----------         
        points: (N,3) ndarray
                The point cloud from wich we want to construct the VoxelGrid.
                Where N is the number of points in the point cloud and the second
                dimension represents the x, y and z coordinates of each point.
        
        x_y_z:  list
                The number of segments in wich each axis will be divided.
                x_y_z[0]: x axis 
                x_y_z[1]: y axis 
                x_y_z[2]: z axis

        bb_cuboid(Optional): bool
                If True(Default):   
                    The bounding box of the point cloud will be adjusted
                    in order to have all the dimensions of equal lenght.                
                If False:
                    The bounding box is allowed to have dimensions of different sizes.
        """
        self.points = points
        xyzmin = np.min(points, axis=0)
        xyzmax = np.max(points, axis=0)

        if bb_cuboid:
            #: adjust to obtain a  minimum bounding box with all sides of equal lenght 
            diff = max(xyzmax-xyzmin) - (xyzmax-xyzmin)
            xyzmin = xyzmin - diff / 2
            xyzmax = xyzmax + diff / 2 

        self.xyzmin = xyzmin
        self.xyzmax = xyzmax
        segments = []
        shape = []

        for i in range(3):
            # note the +1 in num 
            if type(x_y_z[i]) is not int:
                raise TypeError("x_y_z[{}] must be int".format(i))
            s, step = np.linspace(xyzmin[i], xyzmax[i], num=(x_y_z[i] + 1), retstep=True)
            segments.append(s)
            shape.append(step)
            
        self.segments = segments
        self.shape = shape
        self.n_voxels = x_y_z[0] * x_y_z[1] * x_y_z[2]
        self.n_x = x_y_z[0]
        self.n_y = x_y_z[1]
        self.n_z = x_y_z[2]
        self.id = "V([{},{},{}],{})".format(x_y_z[0], x_y_z[1], x_y_z[2], bb_cuboid)
        self.build()

    def build(self):
        # find where each point lies in corresponding segmented axis
        # -1 so index are 0-based; clip for edge cases
        self.voxel_x = np.clip(np.searchsorted(self.segments[0], self.points[:,0]) - 1, 0, self.n_x)
        self.voxel_y = np.clip(np.searchsorted(self.segments[1], self.points[:,1]) - 1, 0, self.n_y)
        self.voxel_z = np.clip(np.searchsorted(self.segments[2], self.points[:,2]) - 1, 0, self.n_z) 
        self.voxel_n = np.ravel_multi_index([self.voxel_x, self.voxel_y, self.voxel_z], [self.n_x, self.n_y, self.n_z])

        # compute center of each voxel
        midsegments = [(self.segments[i][1:] + self.segments[i][:-1]) / 2 for i in range(3)]
        self.voxel_centers = cartesian(midsegments)

    def get_feature_vector(self, mode="binary"):

        if mode == "binary":
            vector = np.zeros(self.n_x * self.n_y * self.n_z)
            vector[np.unique(self.voxel_n)] = 1
            return vector.reshape((self.n_x, self.ny, self.nz))

        elif mode == "density":
            vector = np.zeros(self.n_x * self.n_y * self.n_z)
            count = np.bincount(self.voxel_n)
            vector[:len(count)] = count
            vector /= len(self.voxel_n)
            return vector.reshape((self.n_x, self.ny, self.nz))

        elif mode == "TDF":
            truncation = np.linalg.norm(self.shape)
            kdt = cKDTree(self.points)
            d, i =  kdt.query(self.voxel_centers, n_jobs=-1)
            return d.reshape((self.n_x, self.ny, self.nz))

    def plot_feature_vector(self, mode="binary", d=2, cmap="Oranges"):
        feature_vector = self.get_feature_vector(mode)
        
        if d == 2:
            fig, axes= plt.subplots(int(np.ceil(self.n_z / 4)), 4, figsize=(8,8))
            plt.tight_layout()
            for i, ax in enumerate(axes.flat):
                if i >= len(feature_vector):
                    break
                im = ax.imshow(feature_vector[i], cmap=cmap, interpolation="none")
                ax.set_title("Level " + str(i))
            fig.subplots_adjust(right=0.8)
            cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
            cbar = fig.colorbar(im, cax=cbar_ax)
            cbar.set_label(mode.upper())
            
        elif d == 3:
            return plot_voxelgrid(self, cmap=cmap)

