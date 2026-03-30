import os
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from core.testes.pipeline import pipeline
import zipfile
import pandas as pd
from io import BytesIO

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

@app.route("/process", methods=["POST"])
def process_image():
    file = request.files.get("file")

    image_path = os.path.join(INPUT_DIR, file.filename)
    file.save(image_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_name = Path(file.filename).stem
    output_subdir = os.path.join(OUTPUT_DIR, f"{upload_name}_{timestamp}")
    os.makedirs(output_subdir, exist_ok=True)

    outputs = pipeline(image_path, output_subdir)

    output_urls = [
        f"http://localhost:5000/files/{os.path.basename(output_subdir)}/{os.path.basename(f)}"
        for f in outputs
    ]

    resumo_path = os.path.join(output_subdir, "resumo.csv")
    resumo_data = pd.read_csv(resumo_path, encoding="latin1").to_dict(orient="records")

    return jsonify({
        "status": "ok",
        "results": output_urls,
        "resumo": resumo_data
    })


@app.route("/files/<subdir>/<filename>")
def serve_file(subdir, filename):
    dir_path = os.path.join(OUTPUT_DIR, subdir)
    return send_from_directory(dir_path, filename)

@app.route("/download_csvs/<path:subdir>")
def download_csvs(subdir):
    try:
        dir_path = os.path.join(OUTPUT_DIR, subdir)
        
        if not os.path.exists(dir_path):
            return jsonify({"error": "Diretório não encontrado"}), 404
        
        # Criar ZIP em memória
        from io import BytesIO
        memory_file = BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in ["resumo.csv", "resultados.csv"]:
                file_path = os.path.join(dir_path, filename)
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=filename)
        
        memory_file.seek(0)
        
        from flask import send_file
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"csvs_{os.path.basename(subdir)}.zip"
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)