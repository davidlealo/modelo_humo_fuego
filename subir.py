import os
from pathlib import Path
from dotenv import load_dotenv
from roboflow import Roboflow

# Cargar variables de entorno
load_dotenv()

# API Key (asegúrate de que tu .env tenga ROBOFLOW_API_KEY=tu_api_key)
api_key = os.getenv("ROBOFLOW_API_KEY") or os.getenv("roboflow_api_key")
if not api_key:
    raise ValueError("No se encontró la API Key. Define ROBOFLOW_API_KEY en tu archivo .env")

# Conectar con Roboflow
rf = Roboflow(api_key=api_key)
workspace = rf.workspace("deteccion-h92uo")
project = workspace.project("humo_detecter-cuzoe")

# Definir carpetas locales
splits = {
    "train": "data/train/images",
    "valid": "data/val/images",
    "test": "data/test/images"
}

# Recorrer splits y subir imágenes
for split, folder in splits.items():
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"⚠️ No existe la carpeta: {folder_path}")
        continue
    
    print(f"\n=== Subiendo imágenes desde {folder_path} al split '{split}' ===")
    for img_file in folder_path.glob("*.jpg"):
        try:
            resp = project.upload(
                image_path=str(img_file),
                split=split,
                num_retry_uploads=3
            )
            print(f"✅ Subida: {img_file.name}")
        except Exception as e:
            print(f"❌ Error con {img_file.name}: {e}")
