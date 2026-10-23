"""Optional CAPWAP AP restart; DRY RUN by default.
CAUTION: A live AP restart causes an outage. Obtain approval first.
"""
import argparse
from common import read_inventory, prompt_login, eventlog

def main():
    p = argparse.ArgumentParser(description="Optional AP restart stage")
    p.add_argument("--inventory", default="examples/ap_inventory.example.csv")
    p.add_argument("--log", default="logs/restart.log")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    rows = read_inventory(args.inventory)
    for row in rows:
        print(f"{'EXECUTE' if args.execute else 'PLAN'} {row['name']}: capwap ap restart")
    if not args.execute:
        print("PLAN ONLY — no AP restarted.")
        return
    from netmiko import ConnectHandler
    creds = prompt_login()
    for row in rows:
        conn = None
        try:
            conn = ConnectHandler(device_type="cisco_ios", host=row["ip"], username=creds.username,
                                  password=creds.password, secret=creds.secret, timeout=30)
            conn.enable()
            output = conn.send_command_timing("capwap ap restart")
            eventlog(args.log, f"[{row['name']}] restart response: {output}")
            if "[confirm]" in output.lower():
                eventlog(args.log, f"[{row['name']}] confirmation sent")
                conn.send_command_timing("")
        except Exception as exc:
            # SSH disconnect may be expected, but should not be treated as successful restart.
            eventlog(args.log, f"[UNVERIFIED] {row['name']} ({row['ip']}): {exc}")
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass
    print("Restart attempted; confirm actual AP status before continuing.")

if __name__ == "__main__":
    main()
