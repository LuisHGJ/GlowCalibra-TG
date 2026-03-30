
import cv2
import numpy as np

def count_drops(imagem_binaria: np.ndarray, proportion: float):
    """
    Conta gotas em uma imagem binária, gera máscara e visualização.
    Retorna:
        - mascara_rotulos (np.ndarray)
        - visualizacao (np.ndarray)
        - dados (list de dicts com Index, X, Y, Area)
    """
    if imagem_binaria is None or imagem_binaria.dtype != np.uint8:
        print("Imagem inválida. Ela deve ser binária (CV_8UC1)!")
        return None, None, []

    # Encontra contornos
    contornos, _ = cv2.findContours(imagem_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Máscara de rótulos e visualização
    mascara_rotulos = np.zeros(imagem_binaria.shape, dtype=np.int32)
    visualizacao = np.zeros((*imagem_binaria.shape, 3), dtype=np.uint8)

    dados = []
    index = 1
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area < 1:
            continue

        M = cv2.moments(contorno)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        area_cm = area * pow(proportion, 2)
        x_cm = round(cx * proportion, 4)
        y_cm = round(cy * proportion, 4)
        # guarda os dados
        dados.append({"Index": index, "X": x_cm, "Y": y_cm, "Area": area_cm, "Diameter" : 2 * np.sqrt(area_cm/np.pi)})

        # desenha na imagem
        cv2.drawContours(visualizacao, [contorno], -1, (255, 255, 255), 1)
        cv2.putText(visualizacao, str(index), (cx - 5, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # preenche a máscara com o índice
        cv2.drawContours(mascara_rotulos, [contorno], -1, index, -1)

        index += 1

    print(f"Total de gotas rotuladas: {index - 1}")
    return mascara_rotulos, visualizacao, dados