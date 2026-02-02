from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from flask import Flask, jsonify, request, send_from_directory, send_file

APP_ROOT = Path(__file__).parent
FRONTEND_DIR = APP_ROOT / "frontend"
HISTORY_FILE = APP_ROOT / "run_history.json"

DEFAULT_INPUT = r"C:\Users\justin\Downloads\Confluence-space-export-220712.html\CD"
DEFAULT_OUTPUT = str(Path.home() / "Desktop" / "scraped-finalized-definitionsv2.csv")
DEFAULT_INVALID = str(Path.home() / "Desktop" / "invalid-links.csv")

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/defaults")
def defaults():
    return jsonify(
        {
            "input": DEFAULT_INPUT,
            "output": DEFAULT_OUTPUT,
            "invalid": DEFAULT_INVALID,
        }
    )


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_history(entries):
    HISTORY_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def add_history_entry(entry):
    entries = load_history()
    entries.insert(0, entry)
    save_history(entries[:25])


def open_directory_dialog():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    selected = filedialog.askdirectory()
    root.destroy()
    return selected


def open_save_dialog(initial_path, title):
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    selected = filedialog.asksaveasfilename(
        initialfile=os.path.basename(initial_path),
        initialdir=os.path.dirname(initial_path),
        title=title,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    root.destroy()
    return selected


@app.get("/history")
def history():
    return jsonify(load_history())


@app.get("/pick-input")
def pick_input():
    selected = open_directory_dialog()
    if not selected:
        return jsonify({"ok": False})
    return jsonify({"ok": True, "path": selected})


@app.get("/pick-output")
def pick_output():
    selected = open_save_dialog(DEFAULT_OUTPUT, "Save Output CSV As")
    if not selected:
        return jsonify({"ok": False})
    return jsonify({"ok": True, "path": selected})


@app.get("/pick-invalid")
def pick_invalid():
    selected = open_save_dialog(DEFAULT_INVALID, "Save Invalid Links CSV As")
    if not selected:
        return jsonify({"ok": False})
    return jsonify({"ok": True, "path": selected})


@app.post("/run")
def run_scraper():
    data = request.get_json(silent=True) or {}
    input_dir = data.get("input") or DEFAULT_INPUT
    output_file = data.get("output") or DEFAULT_OUTPUT
    invalid_file = data.get("invalid") or DEFAULT_INVALID

    if not os.path.isdir(input_dir):
        return jsonify({"ok": False, "error": "Input folder does not exist."}), 400

    cmd = [
        os.fspath(Path(os.environ.get("PYTHON", "python"))),
        "concept-definitions_confluence-scraper-v10.py",
        "--input",
        input_dir,
        "--output",
        output_file,
        "--invalid",
        invalid_file,
    ]

    proc = subprocess.run(cmd, cwd=APP_ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "Scraper failed.",
                    "stderr": proc.stderr.strip(),
                }
            ),
            500,
        )

    add_history_entry(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input": input_dir,
            "output": output_file,
            "invalid": invalid_file,
            "status": "success",
        }
    )

    return jsonify(
        {
            "ok": True,
            "output": output_file,
            "invalid": invalid_file,
        }
    )


@app.get("/download")
def download():
    path = request.args.get("path", "")
    if not path:
        return jsonify({"ok": False, "error": "Missing path."}), 400
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "File not found."}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
