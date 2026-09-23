"""
update_env.py  --  Paste a cURL command, extract Zepto secrets, write to .env

Usage:
    python update_env.py
    (then paste the cURL and press Enter twice, or pipe it in)
"""

import re
import json
import shlex
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console(force_terminal=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

ENV_PATH = Path(__file__).parent / ".env"

# Maps: curl header name  ->  .env key
HEADER_MAP = {
    "cookie":            "ZEPTO_COOKIE",
    "device_id":         "ZEPTO_DEVICE_ID",
    "session_id":        "ZEPTO_SESSION_ID",
    "request_id":        "ZEPTO_REQUEST_ID",
    "request-signature": "ZEPTO_REQUEST_SIGNATURE",
    "x-csrf-secret":     "ZEPTO_CSRF_SECRET",
    "x-xsrf-token":      "ZEPTO_XSRF_TOKEN",
    "x-widget-id":       "ZEPTO_WIDGET_ID",
    "x-timezone":        "ZEPTO_TIMEZONE_HEADER",
    "store_id":          "ZEPTO_STORE_ID",
    "store_ids":         "ZEPTO_STORE_IDS",
}

# Maps: JSON body field  ->  .env key
BODY_MAP = {
    "cartId":    "ZEPTO_CART_ID",
    "storeId":   "ZEPTO_STORE_ID",
    "latitude":  "ZEPTO_LAT",
    "longitude": "ZEPTO_LON",
}


def read_curl_input():
    """Read a (possibly multi-line) cURL command from stdin."""
    if HAS_RICH:
        console.print(Panel(
            "[bold]Paste your cURL command below[/bold]\n"
            "  Right-click in Chrome DevTools -> Copy as cURL (bash)\n"
            "  Then paste here and press [cyan]Enter twice[/cyan] to confirm.",
            title="[bold cyan]Zepto .env Updater[/bold cyan]",
            border_style="bright_blue",
        ))
    else:
        print("\n=== Zepto .env Updater ===")
        print("Paste your cURL command below, then press Enter twice:\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "" and lines:
            break
        lines.append(line)

    # Strip trailing continuation characters from each line BEFORE joining
    # cURL uses \ (bash), ^ (cmd), ` (powershell) for line continuation
    cleaned = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\") or stripped.endswith("^") or stripped.endswith("`"):
            stripped = stripped[:-1]
        cleaned.append(stripped)

    raw = " ".join(cleaned)
    return raw.strip()


def parse_curl(curl_str):
    """Parse a cURL string and extract headers + body."""
    # Remove leading 'curl' if present
    curl_str = re.sub(r"^\s*curl\s+", "", curl_str, count=1)

    try:
        tokens = shlex.split(curl_str, posix=True)
    except ValueError:
        # Fallback: try replacing single quotes with double
        curl_str = curl_str.replace("'", '"')
        tokens = shlex.split(curl_str, posix=True)

    headers = {}
    body = None

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok in ("-H", "--header") and i + 1 < len(tokens):
            header_val = tokens[i + 1]
            if ":" in header_val:
                key, val = header_val.split(":", 1)
                headers[key.strip().lower()] = val.strip()
            i += 2

        elif tok in ("-d", "--data", "--data-raw", "--data-binary") and i + 1 < len(tokens):
            body = tokens[i + 1]
            i += 2

        elif tok in ("-b", "--cookie") and i + 1 < len(tokens):
            # Some cURL exports use -b instead of -H 'Cookie: ...'
            headers["cookie"] = tokens[i + 1]
            i += 2

        elif tok.startswith("-H") and ":" in tok[2:]:
            # Handles -H"Header: value" (no space)
            header_val = tok[2:]
            key, val = header_val.split(":", 1)
            headers[key.strip().lower()] = val.strip()
            i += 1

        else:
            i += 1

    return headers, body


def extract_env_values(headers, body):
    """Build a dict of env key -> value from parsed curl parts."""
    env_values = {}

    # Extract from headers
    for header_name, env_key in HEADER_MAP.items():
        if header_name in headers:
            env_values[env_key] = headers[header_name]

    # Extract from JSON body
    if body:
        try:
            body_json = json.loads(body)
            for body_field, env_key in BODY_MAP.items():
                if body_field in body_json:
                    env_values[env_key] = str(body_json[body_field])
        except json.JSONDecodeError:
            if HAS_RICH:
                console.print("[yellow]>> Could not parse request body as JSON, skipping body fields.[/yellow]")
            else:
                print("Warning: Could not parse request body as JSON, skipping body fields.")

    return env_values


def read_existing_env():
    """Read the current .env file into an ordered dict."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                # Strip surrounding quotes
                val = val.strip().strip('"').strip("'")
                env[key.strip()] = val
    return env


def write_env(env_dict):
    """Write the env dict back to .env file."""
    lines = []
    for key, val in env_dict.items():
        # Quote values that contain spaces or special chars
        if any(c in val for c in " ;=:,"):
            lines.append(f'{key}="{val}"')
        else:
            lines.append(f"{key}={val}")
    lines.append("")  # trailing newline
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    curl_str = read_curl_input()
    if not curl_str:
        if HAS_RICH:
            console.print("[bold red][X] No input received.[/bold red]")
        else:
            print("Error: No input received.")
        sys.exit(1)

    headers, body = parse_curl(curl_str)
    new_values = extract_env_values(headers, body)

    if not new_values:
        if HAS_RICH:
            console.print("[bold red][X] Could not extract any values from the cURL.[/bold red]")
        else:
            print("Error: Could not extract any values from the cURL.")
        sys.exit(1)

    # Merge with existing .env
    existing = read_existing_env()
    updated_keys = []
    new_keys = []

    for key, val in new_values.items():
        if key in existing:
            if existing[key] != val:
                updated_keys.append(key)
        else:
            new_keys.append(key)
        existing[key] = val

    write_env(existing)

    # Display results
    if HAS_RICH:
        table = Table(title="[bold].env Updated[/bold]", border_style="bright_blue", show_lines=True)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="white", max_width=60)
        table.add_column("Status", justify="center")

        for key, val in new_values.items():
            # Truncate long values for display
            display_val = val if len(val) <= 60 else val[:57] + "..."
            if key in updated_keys:
                status = "[bold yellow]UPDATED[/bold yellow]"
            elif key in new_keys:
                status = "[bold green]NEW[/bold green]"
            else:
                status = "[dim]unchanged[/dim]"
            table.add_row(key, display_val, status)

        console.print()
        console.print(table)
        console.print(f"\n[bold green][OK] Wrote {len(new_values)} values to .env[/bold green]")
        if updated_keys:
            console.print(f"  [yellow]{len(updated_keys)} updated[/yellow], ", end="")
        if new_keys:
            console.print(f"  [green]{len(new_keys)} new[/green]", end="")
        console.print()
    else:
        print(f"\nWrote {len(new_values)} values to .env")
        for key in updated_keys:
            print(f"  UPDATED: {key}")
        for key in new_keys:
            print(f"  NEW: {key}")


if __name__ == "__main__":
    main()
