import cv2
import numpy as np

def bitwise_not(image: np.ndarray) -> np.ndarray:
    return cv2.bitwise_not(image)