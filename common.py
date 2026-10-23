"""Shared prompts, CSV validation and logging for wireless migration examples.
No password or SSH secret is intentionally written to disk.
"""
import csv
import getpass
import ipaddress
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_LOG_LOCK = threading.Lock()
_AP_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")

@dataclass(frozen=True)
class Login:
    username: str
    password: str
    secret: str

def prompt_login(with_enable=True):
    username = input("Device username: ").strip()
    if not username:
        raise ValueError("Username is required")
    password = getpass.getpass("Device password: ")
    if not password:
        raise ValueError("Password is required")
    secret = getpass.getpass("Enable secret (Enter to reuse password): ") if with_enable else ""
    return Login(username=username, password=password, secret=secret or password)

def read_inventory(filename, require_platform=False):
    path = Path(filename)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"name", "ip"} | ({"platform"} if require_platform else set())
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Inventory requires columns: {', '.join(sorted(required))}")
        rows = []
        for i, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            ip = (row.get("ip") or "").strip()
            if not _AP_NAME.fullmatch(name):
                raise ValueError(f"Invalid AP name in row {i}: {name!r}")
            try:
                ipaddress.ip_address(ip)
            except ValueError as e:
                raise ValueError(f"Invalid AP IP in row {i}: {ip!r}") from e
            row = {k: (v or "").strip() for k, v in row.items() if k is not None}
            row.update(name=name, ip=ip)
            rows.append(row)
    if not rows:
        raise ValueError("Inventory CSV contains no AP rows")
    return rows

def eventlog(filename, message):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} - {message}\n")
