# This program manipulates distance vectors in the robot coordinate frame,
# as well as arrays of vectors.  Pay attention to format of arguments since
# some functions are not yet optimized to handle numpy [1x2] vectors directly.
# Further functions will be added for rotation of vectors in various coordinate frames.

# Import external libraries
import numpy as np
# from numpy import exp, abs, angle
import time

def getValid(scan):                                 # remove the rows which have invalid distances
    dist = scan[:, 0]                               # store just first column
    angles = scan[:, 1]                             # store just 2nd column
    valid = np.where(dist > 0.016)                  # find values 16mm
    myNums = dist[valid]                            # get valid distances
    myAng = angles[valid]                           # get corresponding valid angles
    output = np.vstack((myNums, myAng))             # recombine columns
    n = output.T                                    # transpose the matrix
    return n


def nearest(scan):                                  # find the nearest point in the scan
    dist = scan[:, 0]                               # store just first column
    column_mins = np.argmin(dist, axis=0)           # get index of min values along 0th axis (columns)
    row_index = column_mins                         # index of the smallest distance
    vec = scan[row_index, :]                        # return the distance and angle of the nearest object in scan
    return vec                                      # contains [r, alpha]


def polar2cart(r, alpha) -> complex:                # convert an individual vector to cartesian coordinates (in the robot frame)
    alpha = np.radians(alpha)                       # alpha*(np.pi/180) # convert to radians
    x = r * np.cos(alpha)                           # get x
    y = r * np.sin(alpha)                           # get y
    return complex(x, y)

def cart2polar(p: complex) -> tuple[float, float]:
    alpha = np.angle(p, deg=True)
    r = abs(p)
    return r, alpha


def rotationMatrix(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array(((c, -s), (s, c)))

def rotate(vec, theta):                             # describe a vector in global coordinates by rotating from body-fixed frame
    R = rotationMatrix(theta)
    vecGlobal = np.matmul(R, vec)                   # multiply the two matrices
    return vecGlobal


def sumVec(vec, loc):                               # add two vectors. (origin to robot, robot to obstacle)
    mySum = vec + loc                               # element-wise addition takes place
    return mySum                                    # return [x,y]


if __name__ == "__main__":
    cart2polar(complex(1, 1))
