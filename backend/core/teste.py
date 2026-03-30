import cv2
import os
import numpy as np  

# Pega o caminho da própria pasta do script
base_path = os.path.dirname(__file__)
img_path = os.path.join(base_path, "a.jpg")

# Carrega a imagem
img = cv2.imread(img_path)
if img is None:
    print(f"Erro: não foi possível carregar a imagem em {img_path}")
else:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    print("Imagem carregada e convertida para HSV com sucesso!")

# Converter para HSV para pegar o azul
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_blue = np.array([100, 50, 50])
upper_blue = np.array([140, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Aplicar máscara circular (2830 px de diâmetro)
mask_circle = np.zeros_like(mask)
center = (mask.shape[1]//2, mask.shape[0]//2)
radius = 2830//2
cv2.circle(mask_circle, center, radius, 255, -1)
mask = cv2.bitwise_and(mask, mask_circle)

# Cobertura em %
coverage = np.sum(mask > 0) / np.sum(mask_circle > 0) * 100
print("Cobertura real: ", coverage)
