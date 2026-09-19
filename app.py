import csv
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

CSV_PATH = os.path.join(os.path.dirname(__file__), "tasks.csv")
FIELDNAMES = ["id", "conteudo", "data_criacao", "status", "data_conclusao"]
MAX_CONTENT_LENGTH = 300


def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_tasks():
    ensure_csv()
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_tasks(tasks):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(tasks)


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    tasks = read_tasks()
    visible = [t for t in tasks if t["status"] != "removida"]
    visible.sort(key=lambda t: t["data_criacao"])
    return jsonify(visible)


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    conteudo = (data.get("conteudo") or "").strip()

    if not conteudo:
        return jsonify({"erro": "Conteudo da tarefa nao pode ser vazio."}), 400
    if len(conteudo) > MAX_CONTENT_LENGTH:
        return jsonify({"erro": f"Conteudo excede {MAX_CONTENT_LENGTH} caracteres."}), 400

    tasks = read_tasks()
    new_task = {
        "id": str(uuid.uuid4()),
        "conteudo": conteudo,
        "data_criacao": now_iso(),
        "status": "pendente",
        "data_conclusao": "",
    }
    tasks.append(new_task)
    write_tasks(tasks)
    return jsonify(new_task), 201


@app.route("/api/tasks/<task_id>/status", methods=["PATCH"])
def update_status(task_id):
    data = request.get_json(silent=True) or {}
    concluida = bool(data.get("concluida"))

    tasks = read_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if target is None:
        return jsonify({"erro": "Tarefa nao encontrada."}), 404

    if concluida:
        target["status"] = "concluida"
        target["data_conclusao"] = now_iso()
    else:
        target["status"] = "pendente"
        target["data_conclusao"] = ""

    write_tasks(tasks)
    return jsonify(target)


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def remove_task(task_id):
    tasks = read_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if target is None:
        return jsonify({"erro": "Tarefa nao encontrada."}), 404

    target["status"] = "removida"
    target["data_conclusao"] = target["data_conclusao"] or now_iso()
    write_tasks(tasks)
    return "", 204


if __name__ == "__main__":
    ensure_csv()
    app.run(debug=True, port=5000)
