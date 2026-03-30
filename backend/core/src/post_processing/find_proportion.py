import cv2
import numpy as np

def find_proportion(radius_px: float, radius_cm: float):
    return (radius_cm / radius_px)