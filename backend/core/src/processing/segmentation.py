import cv2
import numpy as np

def thresholdBinary(image: np.ndarray) -> np.ndarray:
    _, threshold = cv2.threshold(image, 1, 255, cv2.THRESH_BINARY)
    return threshold

def thresholdOtsu(image: np.ndarray) -> np.ndarray:
    _, threshold = cv2.threshold(image, 1, 255, cv2.THRESH_OTSU)
    return threshold

def color_treatment(image: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(image)
    
    b[:] = 0
    g[:] = 0

    noBlue = cv2.merge([b, g, r])

    return noBlue

def grayScale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def segment_components(image: np.ndarray, min_area: int = 20000):
    """
    Aplica connectedComponentsWithStats em image (deve ser imagem binária),
    filtra componentes cuja área >= min_area, e sobrescreve image com
    máscara onde esses componentes grandes são pintados de branco (255) e o resto preto (0).
    """

    if image is None:
        raise ValueError("Nenhuma imagem carregada")

    # Verificar se é grayscale binário
    if len(image.shape) != 2 or image.dtype != np.uint8:
        raise ValueError("self.image precisa ser imagem binária grayscale (cv8U), shape 2D")

    # Aplica connected components with stats
    nLabels, labels, stats, _ = cv2.connectedComponentsWithStats(
        image, connectivity=8, ltype=cv2.CV_32S
    )
    
    # Cria imagem preta
    filtered = np.zeros(image.shape, dtype=np.uint8)

    # Loop ignorando background (label 0)
    for lbl in range(1, nLabels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if area >= min_area:
            filtered[labels == lbl] = 255

    return filtered

def apply_circular_roi(image: np.ndarray, radius: float, center: tuple, margin: float = 10.0):
    """
    Cria uma máscara circular com base no centro/raio encontrados
    e aplica sobre image, sobrescrevendo-a.
    """

    # cria máscara preta
    circMask = np.zeros(image.shape[:2], dtype=np.uint8)

    # desenha círculo branco
    cv2.circle(
        circMask,
        (int(round(center[0])), int(round(center[1]))),
        int(round(radius)),
        255,
        cv2.FILLED
    )

    # aplica máscara à imagem original
    image = cv2.bitwise_and(image, image, mask=circMask)
    return image

def find_center(image: np.ndarray, margin: float = 20.0):
    """
    Usa self.image (binária) para encontrar o centro e o raio aproximado.
    Guarda resultados em self.center e self.finalRadius.
    """
    binMask = image

    assert binMask.dtype == np.uint8 and len(binMask.shape) == 2, \
        "self.image deve ser uma imagem binária 8-bit (CV_8UC1)"

    H, W = binMask.shape
    imgCenter = np.array([W / 2.0, H / 2.0], dtype=np.float32)

    startPoints = [
        (W / 2.0, 0), (W / 2.0, H - 1),
        (0, H / 2.0), (W - 1, H / 2.0),
        (0, 0), (W - 1, 0),
        (0, H - 1), (W - 1, H - 1)
    ]

    hitPoints = []
    for sx, sy in startPoints:
        start = np.array([sx, sy], dtype=np.float32)
        dir_vec = imgCenter - start
        norm = np.linalg.norm(dir_vec)
        if norm == 0:
            continue
        dir_vec /= norm

        t = 0.0
        while t <= norm:
            xi = int(round(start[0] + dir_vec[0] * t))
            yi = int(round(start[1] + dir_vec[1] * t))

            if xi < 0 or xi >= W or yi < 0 or yi >= H:
                break

            if binMask[yi, xi] == 255:
                hitPoints.append(np.array([xi, yi], dtype=np.float32))
                break

            if np.linalg.norm(np.array([xi, yi], dtype=np.float32) - imgCenter) < 1.0:
                hitPoints.append(np.array([xi, yi], dtype=np.float32))
                break

            t += 1.0

    if len(hitPoints) < 3:
        center = tuple(imgCenter)
        finalRadius = 0.0
        return

    center = sum(hitPoints) / len(hitPoints)
    radii = [np.linalg.norm(pt - center) for pt in hitPoints]
    mean = sum(radii) / len(radii)

    filtered = [r for r in radii if abs(r - mean) <= margin]
    finalRadius = sum(filtered) / len(filtered) if filtered else mean

    center = tuple(center)
    finalRadius = float(finalRadius)

    return center, finalRadius

def convertToHSV(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

def createHSVMask(image: np.ndarray, lower_bound: list, upper_bound: list) -> np.ndarray:
    # intervalo de azul-roxo (gotas fluorescentes)
    lower_bound = np.array(lower_bound)
    upper_bound = np.array(upper_bound)

    # criação da máscara
    return cv2.inRange(image, lower_bound, upper_bound)

def applyMask(image: np.ndarray, maskHSV: np.ndarray) -> np.ndarray:
    return cv2.bitwise_and(image, image, mask=maskHSV)

    