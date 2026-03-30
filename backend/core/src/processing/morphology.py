import cv2
import numpy as np

def closing(image: np.ndarray) -> np.ndarray:
    image = cv2.dilate(image, None, iterations=2)
    return cv2.erode(image, None, iterations=2)
