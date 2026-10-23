"""AireOS controller reassignment and AP reset; dry run by default."""
import argparse
import ipaddress
import time
from common import read_inventory, prompt_login

def main():
    p = argparse.ArgumentParser(description="AP primary-controller reassignment (AireOS; change approval required)")
    p.add_argument("--inventory", default="examples/ap_inventory.example.csv")
    p.add_argument("--old-wlc", required=True, help="Current AireOS WLC management IP")
    p.add_argument("--primary-name", required=True, help="Destination controller name")
    p.add_argument("--primary-ip", required=True, help="Destination controller IP")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    for addr in [args.old_wlc, args.primary_ip]:
        try:
            ipaddress.ip_address(addr)
        except ValueError:
            p.error(f"Invalid IP address: {addr}")
    rows = read_inventory(args.inventory)
    for row in rows:
        print(f"{'EXECUTE' if args.execute else 'PLAN'} {row['name']}: config ap primary-base {args.primary_name} {row['name']} {args.primary_ip}; config ap reset {row['name']}")
    if not args.execute:
        print("PLAN ONLY — AP resets not issued. Use --execute only during approved window.")
        return
    from netmiko import ConnectHandler
    login = prompt_login(with_enable=False)
    conn = ConnectHandler(device_type="cisco_wlc", host=args.old_wlc,
                          username=login.username, password=login.password)
    try:
        for row in rows:
            ap = row["name"]
            print(f"[{ap}] configuring primary controller")
            print(conn.send_command(f"config ap primary-base {args.primary_name} {ap} {args.primary_ip}"))
            output = conn.send_command_timing(f"config ap reset {ap}")
            print(output)
            if "Would you like to reset" in output:
                print(conn.send_command_timing("y"))
            time.sleep(1)
    finally:
        conn.disconnect()
    print("Verify AP join and health at destination. Issued commands do not prove success.")

if __name__ == "__main__":
    main()
