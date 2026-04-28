#pip install pyimagej scyjava

"""
Lê as imagens de batch_output/final_images/, aplica Make Binary + Analyze Particles
via pyimagej e salva o Count em batch_output/resultados_imagej.csv
"""

import csv
import os
from pathlib import Path

import imagej

FINAL_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "batch_output", "final_images")
CSV_PATH = os.path.join(os.path.dirname(__file__), "batch_output", "resultados_imagej.csv")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def get_sorted_images(folder):
    files = [
        f for f in Path(folder).iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    # Ordena numericamente pelo stem (1, 2, 3... ao invés de lexicográfico)
    return sorted(files, key=lambda f: int(f.stem))


def analyze_image(ij, image_path: Path) -> int:
    macro = f"""
        open("{str(image_path).replace(os.sep, '/')}");
        run("Make Binary");
        run("Analyze Particles...", "display");
        count = nResults;
        run("Clear Results");
        close("*");
        return "" + count;
    """
    result = ij.py.run_macro(macro)
    count = int(str(result["result"]))
    return count


def main():
    if not os.path.isdir(FINAL_IMAGES_DIR):
        print(f"Pasta não encontrada: {FINAL_IMAGES_DIR}")
        print("Rode batch_process.py primeiro.")
        return

    images = get_sorted_images(FINAL_IMAGES_DIR)
    if not images:
        print("Nenhuma imagem encontrada em batch_output/final_images/")
        return

    print("Iniciando ImageJ (pode demorar na primeira vez)...")
    ij = imagej.init("sc.fiji:fiji", mode="headless")
    print(f"ImageJ {ij.getVersion()} pronto.\n")

    rows = []

    for img_path in images:
        image_id = img_path.stem  # "1", "2", "3"...
        print(f"Processando imagem {image_id}...")
        try:
            count = analyze_image(ij, img_path)
            print(f"  -> Count: {count}")
            rows.append({"Imagem": image_id, "Count": count})
        except Exception as e:
            print(f"  [ERRO] {e}")
            rows.append({"Imagem": image_id, "Count": "ERRO"})

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Imagem", "Count"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nConcluído. CSV salvo em: {CSV_PATH}")


if __name__ == "__main__":
    main()
