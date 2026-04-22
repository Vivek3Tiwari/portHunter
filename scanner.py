import ipaddress
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from pathlib import Path

import nmap


# Constants
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str(BASE_DIR / "database.db")
SCAN_TIMEOUT_SECONDS = 60
PORT_RANGE = "1-1024"


def init_db():
    """Create the scans table if it does not already exist."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_ip TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open_ports TEXT NOT NULL
            )
            """
        )
        connection.commit()


def validate_ip(target_ip):
    """Validate and normalize the IP address."""
    if not target_ip or not isinstance(target_ip, str):
        raise ValueError("Target IP address is required.")

    try:
        return str(ipaddress.ip_address(target_ip.strip()))
    except ValueError as exc:
        raise ValueError("Invalid IP address provided.") from exc


def _run_nmap_scan(target_ip):
    """Run Nmap scan and return structured results."""
    scanner = nmap.PortScanner()
    arguments = f"-sV -T4 --host-timeout {SCAN_TIMEOUT_SECONDS}s"

    try:
        scanner.scan(hosts=target_ip, ports=PORT_RANGE, arguments=arguments)
    except nmap.PortScannerError as exc:
        raise RuntimeError(f"Nmap execution failed: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected scan error: {exc}") from exc

    # Default response
    result = {
        "host_ip": target_ip,
        "status": "down",
        "open_ports": [],
    }

    if target_ip not in scanner.all_hosts():
        return result

    result["status"] = scanner[target_ip].state()

    for protocol in scanner[target_ip].all_protocols():
        for port in sorted(scanner[target_ip][protocol].keys()):
            port_info = scanner[target_ip][protocol][port]

            if port_info.get("state") != "open":
                continue

            result["open_ports"].append({
                "port": port,
                "service": port_info.get("name", "unknown") or "unknown",
            })

    return result


def save_scan_result(target_ip, timestamp, open_ports):
    """Save scan result into SQLite database."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO scans (target_ip, timestamp, open_ports)
            VALUES (?, ?, ?)
            """,
            (target_ip, timestamp, json.dumps(open_ports)),
        )
        connection.commit()


def scan_target(target_ip, timeout=SCAN_TIMEOUT_SECONDS):
    """Validate IP, perform scan, store result, and return data."""
    normalized_ip = validate_ip(target_ip)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_nmap_scan, normalized_ip)

        try:
            scan_result = future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TimeoutError("Scan timed out while waiting for Nmap.") from exc

    timestamp = datetime.now(timezone.utc).isoformat()

    save_scan_result(normalized_ip, timestamp, scan_result["open_ports"])

    scan_result["timestamp"] = timestamp
    return scan_result


def get_scan_history():
    """Fetch all previous scan results from database."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT target_ip, timestamp, open_ports FROM scans ORDER BY id DESC"
        )

        rows = cursor.fetchall()

    history = []
    for target_ip, timestamp, open_ports in rows:
        history.append({
            "target_ip": target_ip,
            "timestamp": timestamp,
            "open_ports": json.loads(open_ports),
        })

    return history
