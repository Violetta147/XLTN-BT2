"""Export every saved Jupyter cell output into working_output/.

The original output object is always retained as JSON. Common MIME payloads
are also written as directly viewable files for inspection.
"""

import base64
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEST = ROOT / "working_output"
MIME_EXTENSIONS = {
    "text/plain": ".txt",
    "text/html": ".html",
    "text/markdown": ".md",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
    "application/json": ".json",
    "application/vnd.jupyter.widget-view+json": ".widget.json",
    "application/vnd.google.colaboratory.intrinsic+json": ".colab.json",
}


def joined(value):
    return "".join(value) if isinstance(value, list) else value


def write_payload(path, payload, binary=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(base64.b64decode(joined(payload)))
    elif isinstance(payload, (dict, list)) and not (
        isinstance(payload, list) and all(isinstance(item, str) for item in payload)
    ):
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(joined(payload), encoding="utf-8")


def main():
    manifest = {"notebooks": []}
    for notebook_path in sorted(ROOT.glob("*.ipynb")):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook_dir = DEST / notebook_path.stem
        record = {
            "name": notebook_path.name,
            "sha256": hashlib.sha256(notebook_path.read_bytes()).hexdigest(),
            "cells": len(notebook["cells"]),
            "outputs": [],
        }
        for cell_index, cell in enumerate(notebook["cells"]):
            for output_index, output in enumerate(cell.get("outputs", [])):
                prefix = notebook_dir / f"cell_{cell_index:02d}" / f"output_{output_index:02d}"
                raw_path = prefix.with_suffix(".json")
                write_payload(raw_path, output)
                files = [raw_path.relative_to(DEST).as_posix()]
                if "text" in output:
                    path = prefix.with_suffix(".stream.txt")
                    write_payload(path, output["text"])
                    files.append(path.relative_to(DEST).as_posix())
                if "traceback" in output:
                    path = prefix.with_suffix(".traceback.txt")
                    write_payload(path, "\n".join(output["traceback"]))
                    files.append(path.relative_to(DEST).as_posix())
                for mime, payload in output.get("data", {}).items():
                    extension = MIME_EXTENSIONS.get(mime)
                    if extension is None:
                        extension = "." + mime.replace("/", "_").replace("+", "_")
                    path = prefix.with_suffix(extension)
                    write_payload(path, payload, binary=mime in {"image/png", "image/jpeg"})
                    files.append(path.relative_to(DEST).as_posix())
                record["outputs"].append({
                    "cell": cell_index,
                    "index": output_index,
                    "type": output.get("output_type"),
                    "mime_types": list(output.get("data", {})),
                    "files": files,
                })
        manifest["notebooks"].append(record)
    DEST.mkdir(exist_ok=True)
    (DEST / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for record in manifest["notebooks"]:
        print(f"{record['name']}: {len(record['outputs'])} outputs")
    print("Saved to", DEST)


if __name__ == "__main__":
    main()
