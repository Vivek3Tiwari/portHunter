import logging
import os
import socket
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from scanner import init_db, scan_target, get_scan_history


BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("porthunter")

# Initialize database
init_db()


# ✅ Frontend route
@app.route("/", methods=["GET"])
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css", methods=["GET"])
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js", methods=["GET"])
def script():
    return send_from_directory(BASE_DIR, "script.js")


# ✅ Health check route
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"message": "PortHunter Backend Running"}), 200


# ✅ Scan API
@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True) or {}
    target_ip = data.get("target_ip")

    if not target_ip:
        return jsonify({"error": "target_ip is required"}), 400

    logger.info("Scan request received for target_ip=%s", target_ip)

    try:
        result = scan_target(target_ip)
        response = {
            "host_ip": result.get("host_ip"),
            "status": result.get("status"),
            "open_ports": result.get("open_ports", []),
            "timestamp": result.get("timestamp"),
        }
        return jsonify(response), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    except TimeoutError as exc:
        return jsonify({"error": str(exc)}), 408

    except Exception:
        logger.exception("Unexpected error during scan for %s", target_ip)
        return jsonify({"error": "Internal server error"}), 500


# ✅ History API (NEW 🔥)
@app.route("/history", methods=["GET"])
def history():
    try:
        data = get_scan_history()
        return jsonify(data), 200
    except Exception:
        return jsonify({"error": "Failed to fetch history"}), 500


def get_available_port(preferred_port):
    """Use the preferred port when possible, otherwise find a free local port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", preferred_port))
            return preferred_port
        except OSError:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]


# Run server
if __name__ == "__main__":
    requested_port = int(os.environ.get("PORT", "8000"))
    port = get_available_port(requested_port)

    if port != requested_port:
        logger.warning(
            "Port %s is unavailable. Starting PortHunter on port %s instead.",
            requested_port,
            port,
        )
    else:
        logger.info("Starting PortHunter on port %s.", port)

    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        host="127.0.0.1",
        port=port,
        use_reloader=False,
    )
