import cv2
import os
import numpy as np
from pathlib import Path
from ..src.IO.file_management import load_image, save_image, export_csv
from ..src.processing.filters import blur, laplacian
from ..src.processing.logical_ops import bitwise_not
from ..src.processing.segmentation import (
    apply_circular_roi, color_treatment, segment_components, thresholdBinary,
    find_center, grayScale, applyMask, convertToHSV, createHSVMask, thresholdOtsu
)
from ..src.processing.morphology import closing
from ..src.post_processing.count_drops import count_drops
from ..src.post_processing.find_proportion import find_proportion  

DIAMETER_CM = 5

def pipeline(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    image = load_image(image_path)

    mask = color_treatment(image)
    save_image(mask, os.path.join(output_dir, "color_treatment.jpg"))

    mask = grayScale(mask)
    save_image(mask, os.path.join(output_dir, "gray_scale.jpg"))

    mask = blur(mask, (11, 11))
    mask = thresholdBinary(mask)
    save_image(mask, os.path.join(output_dir, "threshold_binary.jpg"))

    mask = blur(mask, (9, 9))
    mask = bitwise_not(mask)
    save_image(mask, os.path.join(output_dir, "bitwise_not.jpg"))

    mask = segment_components(mask)
    
    margin = 20
    center, radius = find_center(mask, margin)
    effective_radius = radius - margin 

    proportion = find_proportion(radius_cm=(DIAMETER_CM / 2), radius_px=effective_radius)

    image = apply_circular_roi(image, effective_radius, center, margin=0) 
    save_image(image, os.path.join(output_dir, "final_mask.jpg"))

    image = convertToHSV(image)
    hsvMask = createHSVMask(image, [90, 50, 50], [160, 255, 255])
    image = applyMask(image, hsvMask)

    image = grayScale(image)
    image = thresholdOtsu(image)
    save_image(image, os.path.join(output_dir, "final_threshold.jpg"))

    image = closing(image)
    save_image(image, os.path.join(output_dir, "final_image.jpg"))

    circMask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.circle(circMask,
               (int(round(center[0])), int(round(center[1]))),
               int(round(effective_radius)), 255, cv2.FILLED)
    image = cv2.bitwise_and(image, circMask)

    mask, vis, data = count_drops(image, proportion)
    save_image(vis, os.path.join(output_dir, "vis.jpg"))
    export_csv(os.path.join(output_dir, "resultados.csv"), data)

    radius_cm = DIAMETER_CM / 2  
    area_total = np.pi * (radius_cm ** 2)
    num_drops = len(data)
    area_gotas_total = sum(d["Area"] for d in data)

    densidade = round(num_drops / area_total, 2)
    cobertura = round((area_gotas_total / area_total) * 100, 2)

    print(f"\n--- Resultados ---")
    print(f"Total de gotas: {num_drops}")
    print(f"Densidade: {densidade:.2f} gotas/cm²")
    print(f"Cobertura: {cobertura:.2f}%")

    resumo_path = os.path.join(output_dir, "resumo.csv")
    with open(resumo_path, "w", newline="", encoding="utf-8") as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(["Total gotas", "Densidade (gotas/cm²)", "Cobertura (%)"])
        writer.writerow([num_drops, densidade, cobertura])
    
    outputs = [
        "final_image.jpg",
        "vis.jpg",
        "resultados.csv",
        "resumo.csv"
    ]

    return [os.path.join(output_dir, f) for f in outputs]

if __name__ == "__main__": 
    pipeline()