import os
from pathlib import Path
from dotenv import load_dotenv
from roboflow import Roboflow

load_dotenv()
API_KEY = os.getenv("ROBOFLOW_API_KEY") or os.getenv("roboflow_api_key")
if not API_KEY:
    raise RuntimeError("No se encontró ROBOFLOW_API_KEY en el .env")

rf = Roboflow(api_key=API_KEY)
workspace = rf.workspace("deteccion-h92uo")
project   = workspace.project("humo_detecter-cuzoe")

SPLITS = {
    "train": ("data/train/images", "data/train/labels"),
    "valid": ("data/val/images",   "data/val/labels"),
    "test":  ("data/test/images",  "data/test/labels"),
}
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

for split, (img_dir, lbl_dir) in SPLITS.items():
    img_dir, lbl_dir = Path(img_dir), Path(lbl_dir)
    if not img_dir.exists():
        print(f"⚠️ No existe {img_dir} (split {split})")
        continue

    print(f"\n=== Subiendo {split} con anotaciones YOLO (si existen) ===")
    for img_path in img_dir.iterdir():
        if not (img_path.is_file() and img_path.suffix.lower() in EXTS):
            continue
        label_path = lbl_dir / (img_path.stem + ".txt")
        kwargs = dict(image_path=str(img_path), split=split, num_retry_uploads=3)
        if label_path.exists():
            kwargs["annotation_path"] = str(label_path)  # ← etiqueta YOLO acompañando la imagen

        try:
            project.upload(**kwargs)
            print(f"✅ {img_path.name}  {'(+ label)' if label_path.exists() else '(solo imagen)'}")
        except Exception as e:
            print(f"❌ {img_path.name}: {e}")
