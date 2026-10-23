# Wireless Controller Migration — Practical Cisco AP Automation Scripts

**Author:** Abraham Akindoyin  
**Status:** Historical engineering scripts adapted for public review. This is an educational/engineering reference, **not** a polished or universally supported migration tool.

## Background: learning from the Georgia remote site

During initial wireless-controller migration work at three sites, including a remote site in Georgia, AP software image transfers took approximately **90 minutes per AP**, by the author's recollection. The site had a nominal **100 Mbps up/down circuit**. The experience raised an operational challenge: repeating manual AP preparation and verification at additional remote sites could put maintenance windows at risk.

Circuit rate or geographic distance alone does **not** prove the reason for the delays. Latency, transfer protocol, concurrency, image size, traffic contention, and server placement were not individually benchmarked.

Following that experience, I developed a small collection of Python/Netmiko scripts to simplify **image staging, parallelized image-integrity output collection, controlled restarts, and controller reassignment**. The goal was repeatability and less manual effort, not inventing wireless predownload technology. Established Cisco workflows and tools, including WLAN Poller, address related needs; these scripts reflect my specific deployment workflow and constraints.

An external wireless CCIE participated in only the initial **three** sites, including Georgia. His firsthand observations of those sites are separate from any later review of these scripts or the subsequent migrations. My manager separately described the broader **13-building overnight migration** in a performance review, but this repository does **not** quantify speedup or prove these scripts alone produced that outcome.

## Practical workflow and file map

| Stage | File | Function | What it does not guarantee |
|---|---|---|---|
| 0 — Plan | `examples/ap_inventory.example.csv` | Define AP names, management addresses and models; prepare maintenance approvals | Image/platform compatibility or site readiness |
| 1 — Stage | `image-predownload.py` | Model-specific filename mapping; `archive download-sw /no-reload`; four workers by default | Successful transfer or transfer time |
| 2 — Observe | `verify-download.py` | Concurrent `show image integrity` collection using channel/prompt polling | Automated integrity PASS/FAIL |
| 2 (alternative) — Observe | `verify-dwnld-10s.py` | Concurrent integrity-output collection, plus a 10-second buffer wait per worker | A 10-second fleet-wide result |
| 3 — Restart (optional) | `reload-post-img-predwld.py` | Issue `capwap ap restart` in sequence | Verified reboot, join, client health |
| 4 — Reassign | `migration_script.py` | AireOS `config ap primary-base` and AP reset commands | Validated join on new controller |
| 5 — Validate | Manual / existing controllers | Check AP join, image, service, radio health and rollback readiness | Not implemented in these scripts |

The actual stage order and applicable commands depend on controller/AP platform, versions, deployment plan and image compatibility. These scripts are **separate building blocks, not an unconditionally safe one-click migration**. A live deployment requires approval, compatibility checks, site-specific sequencing and rollback procedures.

## What changed from the historical versions?

These are **adapted copies** of scripts I developed during the wireless project, not byte-for-byte copies of the originals.

- Added `input()` for the device username and `getpass.getpass()` for password and enable secret at execution time.
- Made TFTP server, controller names/IPs, inventory path, and other settings configurable instead of retaining company-specific values.
- Replaced the source inventory with **fictional RFC 5737 documentation IP addresses**.
- Added explicit `--execute` opt-in; **without it, scripts only print planned actions** and do not open live device sessions.
- Excluded runtime logs, caches, and credentials files from Git.
- Kept original command patterns and basic concurrency/mapping choices, with their limitations documented.

These adaptations have passed basic syntax checks, three offline unit tests and plan-only command checks. They have **not been revalidated here on live Cisco controllers or access points**.

## Quick start (Windows PowerShell)

Python 3.10+ is recommended. The plan-only examples do not need a device connection. For live Netmiko execution install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run these dry-run examples from the repository's root:

```powershell
python image-predownload.py --tftp-server 192.0.2.10
python verify-download.py
python verify-dwnld-10s.py
python reload-post-img-predwld.py
python migration_script.py --old-wlc 192.0.2.100 --primary-name DEMO-WLC --primary-ip 192.0.2.101
python -m unittest discover -s tests -v
```

**All commands above are PLAN ONLY.** Nothing attempts a real network change without `--execute`. Live changes should be undertaken only on devices you are authorized to manage, using real validated inventory/configuration and an approved change plan. When executing, the scripts prompt for the username, hidden password, and, where needed, hidden enable secret.

## Technical limitations and possible improvements

1. The historical image-prestage routine uses a 60-second delay but does **not** confirm transfer completion; manual post-checks are required.
2. `verify-dwnld-10s.py` uses up to ten concurrent workers and a ten-second channel buffer wait — **not** a ten-second total run-time guarantee. Both verification variants collect raw integrity outputs, without robust automatic pass/fail parsing.
3. The code mixes platform-specific Cisco IOS AP commands with legacy AireOS WLC commands. Support varies by device type, version and architecture.
4. Parallel TFTP/image delivery is not always faster: insufficient WAN capacity, server limits and concurrent flows can create contention.
5. No comprehensive model/firmware eligibility checks, disk-space preflights, AP-join health validation, transaction-safe rollback, bounded retry policy, or measured transfer benchmarks are included.
6. Prompt-based reads and time-based collection can miss slow/truncated outputs; operational success cannot be inferred from a command returning without raising an exception.
7. Logs could contain device output and internal details; never commit real operational logs or credentials to this repository.

## Relevance to ongoing engineering development

The contribution I wish to explore further is the **repeatable engineering workflow**: use observed migration constraints to make multi-device infrastructure changes easier to stage, inspect and verify, then improve the tooling through explicit evidence and testing. This is complementary to my publicly documented multi-plane network fault-isolation work, while remaining a separate project.

See [REVIEW_FOR_REZA.md](REVIEW_FOR_REZA.md) for a bounded technical-review context note. Reviewers are free to critique the workflow and are not being asked to confirm work they did not personally observe.

## Intellectual property and safety

No external source code license is granted by this repository at present. Publication of sanitized code does not, by itself, resolve possible employer IP or external-sharing restrictions. Only use this material where you have confirmed appropriate permissions. **Do not use the examples for production network changes without independent engineering review.**
