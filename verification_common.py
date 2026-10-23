"""Two historical approaches for collecting image-integrity output in parallel.
Neither implementation parses the output to establish PASS/FAIL.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import time
from common import read_inventory, prompt_login, eventlog

def collect_until_prompt(conn, max_wait_seconds=10, read_interval=0.5, prompt="#"):
    output = ""
    end = time.monotonic() + max_wait_seconds
    while time.monotonic() < end:
        time.sleep(read_interval)
        chunk = conn.read_channel()
        if chunk:
            output += chunk
            if prompt in chunk:
                break
    return output

def run_variant(mode):
    p = argparse.ArgumentParser(description=f"Parallel image-integrity output collection: {mode}")
    p.add_argument("--inventory", default="examples/ap_inventory.example.csv")
    p.add_argument("--threads", type=int, default=10)
    p.add_argument("--log", default=f"logs/verify_{mode}.log")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if args.threads < 1 or args.threads > 20:
        p.error("--threads must be between 1 and 20")
    rows = read_inventory(args.inventory)
    for row in rows:
        print(f"{'EXECUTE' if args.execute else 'PLAN'} {row['name']}: show image integrity ({mode})")
    if not args.execute:
        print("PLAN ONLY. Ten workers by default; 10s is NOT a fleet-wide runtime guarantee.")
        return
    from netmiko import ConnectHandler
    creds = prompt_login()
    def worker(row):
        conn = None
        try:
            conn = ConnectHandler(device_type="cisco_ios", host=row["ip"],
                                  username=creds.username, password=creds.password,
                                  secret=creds.secret, timeout=30)
            conn.enable()
            if mode == "poll":
                conn.write_channel("show image integrity\n")
                output = collect_until_prompt(conn)
            else:
                output = conn.send_command_timing("show image integrity", read_timeout=60)
                # Original 10s variant used an additional 10s buffer read.
                time.sleep(10)
                output += conn.read_channel()
            eventlog(args.log, f"[{row['name']}] raw output (NOT graded):\n{output}")
            print(f"COLLECTED {row['name']} (not verified pass/fail)")
        except Exception as exc:
            eventlog(args.log, f"[ERROR] {row['name']} ({row['ip']}): {exc}")
            print(f"ERROR {row['name']}")
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        list(pool.map(worker, rows))
    print("Review raw output per AP; manually establish PASS/FAIL.")

