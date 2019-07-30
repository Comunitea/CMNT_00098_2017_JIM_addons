###########################
#  BASIC VOLUME FORMULAS  #
#  By Pablo Luaces        #
#  Coding UTF-8           #
###########################

import math

def calcCubeVolume(width=0.0, height=0.0, depth=0.0):
    if width and height and depth:
        return float(width * height * depth)
    return 0.0

def calcPrismVolume(base_width=0.0, base_height=0.0, height=0.0):
    if base_width and base_height and height:
        return float(base_width * base_height * height)
    return 0.0

def calcPyramidVolume(base_width=0.0, base_height=0.0, height=0.0):
    if base_width and base_height and height:
        return float(base_width * base_height * height / 3)
    return 0.0

def calcCylinderVolume(height=0.0, radius=0.0):
    if height and radius:
        return float(math.pi * radius**2 * height)
    return 0.0

def calcConeVolume(height=0.0, radius=0.0):
    if height and radius:
        return float(math.pi * radius**2 * height / 3)
    return 0.0

def calcSphereVolume(radius=0.0):
    if radius:
        return float(4/3 * math.pi * radius**3)
    return 0.0
