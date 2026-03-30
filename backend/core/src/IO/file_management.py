import cv2
from pathlib import Path
import numpy as np
import csv

def load_image(filename: str) -> np.ndarray:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    path = BASE_DIR / "input" / filename
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Can not open any image on path {path}")
    
    return image
        
def save_image(image: np.ndarray, filename: str) -> str:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent    # pasta onde está o script
    out_dir = BASE_DIR / "output"                     # subpasta "output"
    out_dir.mkdir(parents=True, exist_ok=True)    # cria se não existir

    out_path = out_dir / filename                 # caminho completo do arquivo
    ok = cv2.imwrite(str(out_path), image)   # precisa ser string

    if not ok:
        raise ValueError(f"Erro ao salvar {out_path}")

    return str(out_path)

def export_csv(filename, dados):
    """
    Exporta os dados das gotas para um arquivo CSV, incluindo o diâmetro.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    out_dir = BASE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    with open(out_path, mode="w", newline="") as outFile:
        writer = csv.writer(outFile)
        writer.writerow(["Index", "X", "Y", "Area", "Diameter"])
        for d in dados:
            writer.writerow([d["Index"], d["X"], d["Y"], d["Area"], d["Diameter"]])

    print(f"CSV salvo em {out_path}")