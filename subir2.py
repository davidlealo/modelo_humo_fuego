#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sube una imagen a un proyecto de Roboflow con opciones útiles:
- Lee la API key desde .env (ROBOFLOW_API_KEY, o roboflow_api_key como fallback)
- Permite pasar workspace y project por CLI o .env
- Valida existencia del archivo
- Soporta batch_name, split, tags, retries, sequence_number/size
- Mensajes claros de error/éxito y salida con códigos apropiados
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# --- Dependencia principal ---
try:
    from roboflow import Roboflow
except ImportError as e:
    print("ERROR: Falta la librería 'roboflow'. Instala con: pip install roboflow", file=sys.stderr)
    sys.exit(1)


def get_api_key() -> Optional[str]:
    """
    Intenta cargar la API key desde variables de entorno (con .env).
    Prioriza ROBOFLOW_API_KEY, luego roboflow_api_key (compatibilidad).
    """
    load_dotenv()
    api = os.getenv("ROBOFLOW_API_KEY") or os.getenv("roboflow_api_key")
    return api


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube una imagen a un proyecto de Roboflow."
    )
    parser.add_argument(
        "--workspace", "-w",
        default=os.getenv("ROBOFLOW_WORKSPACE"),
        help="ID/slug del workspace en Roboflow (p.ej., 'my-workspace')."
    )
    parser.add_argument(
        "--project", "-p",
        default=os.getenv("ROBOFLOW_PROJECT"),
        help="ID/slug del proyecto en Roboflow (p.ej., 'my-project')."
    )
    parser.add_argument(
        "--image", "-i",
        required=True,
        help="Ruta a la imagen a subir (JPG/PNG, etc.)."
    )
    parser.add_argument(
        "--batch-name", "-b",
        dest="batch_name",
        default=None,
        help="Nombre del batch para organizar subidas (opcional)."
    )
    parser.add_argument(
        "--split", "-s",
        choices=["train", "valid", "test"],
        default=None,
        help="Split del dataset al que se subirá la imagen (opcional)."
    )
    parser.add_argument(
        "--tags", "-t",
        nargs="*",
        default=None,
        help="Lista de tags/etiquetas a agregar (opcional). Ej: --tags perro calle noche"
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=3,
        help="Cantidad de reintentos en caso de fallo de subida (por defecto: 3)."
    )
    parser.add_argument(
        "--seq-num",
        type=int,
        dest="sequence_number",
        default=None,
        help="Número de secuencia (opcional) para preservar orden."
    )
    parser.add_argument(
        "--seq-size",
        type=int,
        dest="sequence_size",
        default=None,
        help="Tamaño total de la secuencia (opcional)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = get_api_key()
    if not api_key:
        print(
            "ERROR: No se encontró la API key.\n"
            "Define ROBOFLOW_API_KEY en tu entorno o en un archivo .env",
            file=sys.stderr
        )
        sys.exit(2)

    if not args.workspace:
        print("ERROR: Debes indicar --workspace o setear ROBOFLOW_WORKSPACE en .env", file=sys.stderr)
        sys.exit(2)

    if not args.project:
        print("ERROR: Debes indicar --project o setear ROBOFLOW_PROJECT en .env", file=sys.stderr)
        sys.exit(2)

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists() or not image_path.is_file():
        print(f"ERROR: La ruta de imagen no existe o no es un archivo: {image_path}", file=sys.stderr)
        sys.exit(3)

    # Inicializa Roboflow
    try:
        rf = Roboflow(api_key=api_key)
    except Exception as e:
        print(f"ERROR: No se pudo inicializar Roboflow: {e}", file=sys.stderr)
        sys.exit(4)

    # Conecta a workspace y proyecto
    try:
        workspace = rf.workspace(args.workspace)
    except Exception as e:
        print(f"ERROR: No se encontró el workspace '{args.workspace}': {e}", file=sys.stderr)
        sys.exit(5)

    try:
        project = workspace.project(args.project)
    except Exception as e:
        print(f"ERROR: No se encontró el proyecto '{args.project}' en el workspace '{args.workspace}': {e}", file=sys.stderr)
        sys.exit(6)

    # Prepara parámetros opcionales para la subida
    upload_kwargs = {
        "image_path": str(image_path),
        "num_retry_uploads": int(args.retries) if args.retries is not None else None,
        "batch_name": args.batch_name,
        "split": args.split,
        "tag_names": args.tags,
        "sequence_number": args.sequence_number,
        "sequence_size": args.sequence_size,
    }
    # Limpia None para evitar enviar claves vacías
    upload_kwargs = {k: v for k, v in upload_kwargs.items() if v is not None}

    print("=== Subiendo imagen a Roboflow ===")
    print(f"- Workspace: {args.workspace}")
    print(f"- Proyecto:  {args.project}")
    print(f"- Imagen:    {image_path.name}")
    if args.batch_name: print(f"- Batch:     {args.batch_name}")
    if args.split:      print(f"- Split:     {args.split}")
    if args.tags:       print(f"- Tags:      {', '.join(args.tags)}")
    if args.sequence_number is not None:
        print(f"- Secuencia: {args.sequence_number}/{args.sequence_size or '¿desconocido?'}")

    try:
        resp = project.upload(**upload_kwargs)
        # La respuesta suele contener keys útiles como 'id', 'split', 'batch', etc.
        print("\n✅ Subida completada con éxito.")
        print(f"Respuesta del servidor: {resp}")
        # Algunas versiones devuelven un dict; si incluye un enlace, lo mostramos:
        link = None
        if isinstance(resp, dict):
            link = resp.get("image", {}).get("link") or resp.get("link")
        if link:
            print(f"URL de la imagen en Roboflow: {link}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al subir la imagen: {e}", file=sys.stderr)
        sys.exit(7)


if __name__ == "__main__":
    main()
