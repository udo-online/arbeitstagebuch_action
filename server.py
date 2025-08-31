from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)
API_KEY = os.environ.get("ATB_API_KEY", "change-me")

def auth_ok(req) -> bool:
    auth = req.headers.get("Authorization", "")
    return auth.startswith("Bearer ") and auth.split(" ", 1)[1] == API_KEY

@app.post("/tagesblatt")
def tagesblatt():
    if not auth_ok(request): return ("Unauthorized", 401)
    data = request.get_json(force=True)
    # TODO: Hier deine echte PDF-Erzeugung aufrufen (ReportLab)
    # Für den Start geben wir nur eine Dummy-URL zurück:
    return jsonify({"url": "https://example.com/Tagesblatt.pdf"})

@app.post("/woche")
def woche():
    if not auth_ok(request): return ("Unauthorized", 401)
    data = request.get_json(force=True)
    return jsonify({"url": "https://example.com/Woche.pdf"})

@app.post("/gesamt")
def gesamt():
    if not auth_ok(request): return ("Unauthorized", 401)
    data = request.get_json(force=True)
    return jsonify({"url": "https://example.com/Gesamt.pdf"})

@app.get("/")
def root():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
