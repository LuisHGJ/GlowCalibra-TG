import cv2
import numpy as np
from pathlib import Path

def blur(image: np.ndarray, size: tuple) -> np.ndarray:
    return cv2.GaussianBlur(image, size, 2)

def laplacian(image: np.ndarray):
    laplacian = cv2.Laplacian(image, cv2.CV_16S, ksize=5)
    return cv2.convertScaleAbs(laplacian)

