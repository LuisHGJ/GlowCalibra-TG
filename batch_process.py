"""
Automação: processa todas as imagens da pasta Fotos em ordem,
salva as final_image.jpg numeradas e gera um CSV consolidado.
"""

import os
import sys
import csv
import shutil
import tempfile
from pathlib import Path

# Adiciona o backend ao path para importar a pipeline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from core.testes.pipeline import pipeline

FOTOS_DIR = os.path.join(os.path.dirname(__file__), "Fotos")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "batch_output")
FINAL_IMAGES_DIR = os.path.join(OUTPUT_DIR, "final_images")
CSV_PATH = os.path.join(OUTPUT_DIR, "resultados_consolidados.csv")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def get_sorted_images(folder):
    files = [
        f for f in Path(folder).iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda f: f.name)


def main():
    os.makedirs(FINAL_IMAGES_DIR, exist_ok=True)

    images = get_sorted_images(FOTOS_DIR)
    if not images:
        print("Nenhuma imagem encontrada em Fotos/")
        return

    print(f"Encontradas {len(images)} imagens. Iniciando processamento...\n")

    csv_rows = []

    for idx, img_path in enumerate(images, start=1):
        print(f"[{idx}/{len(images)}] Processando: {img_path.name}")

        # Diretório temporário para os artefatos intermediários
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                outputs = pipeline(str(img_path), tmp_dir)

                # Copia a final_image.jpg com o ID como nome
                final_img_src = os.path.join(tmp_dir, "final_image.jpg")
                final_img_dst = os.path.join(FINAL_IMAGES_DIR, f"{idx}.jpg")
                shutil.copy2(final_img_src, final_img_dst)

                # Lê o resumo.csv gerado pela pipeline
                resumo_path = os.path.join(tmp_dir, "resumo.csv")
                with open(resumo_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    row = next(reader)
                    csv_rows.append({
                        "Imagem": idx,
                        "Numero de gotas": row["Total gotas"],
                        "Densidade (gotas/cm²)": row["Densidade (gotas/cm²)"],
                        "Cobertura (%)": row["Cobertura (%)"],
                    })

                print(f"  -> Gotas: {row['Total gotas']} | Densidade: {row['Densidade (gotas/cm²)']} | Cobertura: {row['Cobertura (%)']}%")

            except Exception as e:
                print(f"  [ERRO] Falha ao processar {img_path.name}: {e}")
                csv_rows.append({
                    "Imagem": idx,
                    "Numero de gotas": "ERRO",
                    "Densidade (gotas/cm²)": "ERRO",
                    "Cobertura (%)": "ERRO",
                })

    # Salva CSV consolidado
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Imagem", "Numero de gotas", "Densidade (gotas/cm²)", "Cobertura (%)"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nConcluído.")
    print(f"  Imagens finais: {FINAL_IMAGES_DIR}")
    print(f"  CSV consolidado: {CSV_PATH}")


if __name__ == "__main__":
    main()
