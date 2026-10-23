"""Prestage AP image commands; dry-run until --execute.
This does not confirm that any image transfer completed.
"""
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from common import prompt_login, read_inventory, eventlog

PREFIXES = {"2802": "ap3g3", "1852": "ap1g4", "9130": "ap1g6a"}

def get_image_prefix(model):
    for key, value in PREFIXES.items():
        if key in model.upper():
            return value
    return None

def build_filename(prefix, version):
    return f"{prefix}-k9w8-tar.{version}.tar"

def plan(row, tftp, version):
    prefix = get_image_prefix(row["platform"])
    if prefix is None:
        return None
    return f"archive download-sw /no-reload tftp://{tftp}/{build_filename(prefix, version)}"

def worker(row, command, creds, log_file, pause):
    from netmiko import ConnectHandler
    name, ip = row["name"], row["ip"]
    conn = None
    try:
        conn = ConnectHandler(device_type="cisco_ios", host=ip, username=creds.username,
                              password=creds.password, secret=creds.secret, timeout=30)
        conn.enable()
        output = conn.send_command_timing(command)
        eventlog(log_file, f"[{name}] Command returned:\n{output}")
        # Historical script paused for 60 s; this does NOT verify successful image staging.
        if pause > 0:
            time.sleep(pause)
        eventlog(log_file, f"[{name}] Session ended; transfer completion NOT verified")
    except Exception as exc:
        eventlog(log_file, f"[ERROR] {name} ({ip}): {exc}")
    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass

def main():
    p = argparse.ArgumentParser(description="Model-aware AP image predownload (verify manually)")
    p.add_argument("--inventory", default="examples/ap_inventory.example.csv")
    p.add_argument("--tftp-server", required=True, help="Image TFTP server address")
    p.add_argument("--image-version", default="17_15_3_28", help="Verify model/version compatibility")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--pause-seconds", type=float, default=60.0)
    p.add_argument("--log", default="logs/predownload.log")
    p.add_argument("--execute", action="store_true", help="Actually connect and launch commands")
    args = p.parse_args()
    if args.threads < 1 or args.threads > 20:
        p.error("--threads must be between 1 and 20")
    if args.pause_seconds < 0:
        p.error("--pause-seconds must be nonnegative")
    rows = read_inventory(args.inventory, require_platform=True)
    jobs = []
    for row in rows:
        cmd = plan(row, args.tftp_server, args.image_version)
        if cmd is None:
            print(f"SKIP {row['name']}: unsupported model {row['platform']}")
            continue
        print(f"{'EXECUTE' if args.execute else 'PLAN'} {row['name']} ({row['ip']}): {cmd}")
        jobs.append((row, cmd))
    if not args.execute:
        print("PLAN ONLY — no connection made. Use --execute after change approval and review.")
        return
    creds = prompt_login()
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        for f in as_completed([pool.submit(worker, row, cmd, creds, args.log, args.pause_seconds)
                               for row, cmd in jobs]):
            f.result()
    print("Commands attempted; independently verify image integrity before proceeding.")

if __name__ == "__main__":
    main()
