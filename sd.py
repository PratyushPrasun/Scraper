import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from parser import find_bank

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
console = Console(force_terminal=True)

URL = "https://bff-gateway.zepto.com/cfs/api/v1/cart/coupons/fetch-list"

REQUIRED_ENV = [
    "ZEPTO_COOKIE", "ZEPTO_CART_ID", "ZEPTO_STORE_ID",
    "ZEPTO_DEVICE_ID", "ZEPTO_SESSION_ID", "ZEPTO_REQUEST_ID",
    "ZEPTO_REQUEST_SIGNATURE", "ZEPTO_CSRF_SECRET", "ZEPTO_XSRF_TOKEN",
    "ZEPTO_WIDGET_ID", "ZEPTO_TIMEZONE_HEADER", "ZEPTO_LAT", "ZEPTO_LON",
]

env = {k: os.environ.get(k) for k in REQUIRED_ENV}
missing = [k for k, v in env.items() if not v]
if missing:
    console.print(f"[bold red][X] Missing from .env:[/bold red] {', '.join(missing)}")
    sys.exit(1)
else:
    console.print("[bold green][OK] All environment variables loaded.[/bold green]")


def build_request():
    payload = {
        "activeTab": "PAYMENT_OFFERS_TAB",
        "filterKey": "Card",
        "renderHeader": False,
        "cartId": env["ZEPTO_CART_ID"],
        "storeId": env["ZEPTO_STORE_ID"],
        "latitude": float(env["ZEPTO_LAT"]),
        "longitude": float(env["ZEPTO_LON"]),
        "useZCoins": False,
        "useZeptoCash": True,
        "removedCampaignProducts": [],
        "installedUpiApps": [],
        "isCredPayEligible": True,
        "enableTabbedView": True,
        "pageType": "COUPON_REVAMP",
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "cookie": env["ZEPTO_COOKIE"],
        "device_id": env["ZEPTO_DEVICE_ID"],
        "deviceid": env["ZEPTO_DEVICE_ID"],
        "session_id": env["ZEPTO_SESSION_ID"],
        "sessionid": env["ZEPTO_SESSION_ID"],
        "request_id": env["ZEPTO_REQUEST_ID"],
        "requestid": env["ZEPTO_REQUEST_ID"],
        "request-signature": env["ZEPTO_REQUEST_SIGNATURE"],
        "x-csrf-secret": env["ZEPTO_CSRF_SECRET"],
        "x-xsrf-token": env["ZEPTO_XSRF_TOKEN"],
        "x-widget-id": env["ZEPTO_WIDGET_ID"],
        "x-timezone": env["ZEPTO_TIMEZONE_HEADER"],
        "store_id": env["ZEPTO_STORE_ID"],
        "storeid": env["ZEPTO_STORE_ID"],
        "store_ids": env.get("ZEPTO_STORE_IDS", env["ZEPTO_STORE_ID"]),
        "store_etas": json.dumps({env["ZEPTO_STORE_ID"]: -1}),
        "auth_from_cookie": "true",
        "auth_revamp_flow": "v2",
        "app_version": "16.31.6",
        "appversion": "16.31.6",
        "compatible_components": ",NEW_BILL_INFO,RE_PROMISE_ETA_ORDER_SCREEN_ENABLED,SUPERSTORE_V1,MANUALLY_APPLIED_DELIVERY_FEE_RECEIVABLE,MARKETPLACE_REPLACEMENT,ZEPTO_PASS:5,CART_REDESIGN_ENABLED,SHIPMENT_WIDGETIZATION_ENABLED,TABBED_CAROUSEL_V2,24X7_ENABLED_V1,PROMO_CASH:0,HOMEPAGE_V2,SUPER_SAVER:1,NO_PLATFORM_CHECK_ENABLED_V2,HP_V4_FEED,GIFT_CARD,SCLP_ADD_MONEY,GIFTING_ENABLED,OFSE,WIDGET_BASED_ETA,PC_REVAMP_1,NEW_ETA_BANNER,NO_COST_EMI_V1,ITEMISATION_ENABLED,SWAP_AND_SAVE_ON_CART,WIDGET_RESTRUCTURE,PRICING_CAMPAIGN_ID,BACHAT_FOR_ALL,TABBED_CAROUSEL_V3,MULTITAB_V2,VERTICAL_FEED_PRODUCT_GRID,CART_LMS:2,SAMPLING_UPSELL_CAMPAIGN,DISCOUNTED_ADDONS_ENABLED,UPSELL_COUPON_SS:0,SIZE_EXCHANGE_ENABLED,ENABLE_FLOATING_CART_BUTTON,SAMPLING_V3,HYBRID_CAMPAIGN,",
        "marketplace_type": "SUPER_SAVER",
        "platform": "WEB",
        "app_sub_platform": "WEB",
        "tenant": "ZEPTO",
        "source": "DIRECT",
        "priority": "u=1, i",
        "origin": "https://www.zepto.com",
        "referer": "https://www.zepto.com/",
        "sec-ch-ua": '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Mobile Safari/537.36",
    }
    return payload, headers


def fetch_raw():
    payload, headers = build_request()
    console.print("[cyan]>> Fetching coupons from Zepto...[/cyan]")
    resp = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=15)
    if resp.status_code == 401:
        console.print("[bold red][X] 401 Unauthorized[/bold red] -- your session/tokens have expired.\n"
                      "  Re-capture the request from DevTools and update .env.")
        sys.exit(1)
    resp.raise_for_status()
    console.print(f"[bold green][OK] Response received[/bold green] -- status {resp.status_code}")
    return resp.json()


def parse_offers(data):
    """Extract offer details from the Zepto API response."""
    offers = []
    widgets = data.get("pageLayout", {}).get("widgets", [])
    for w in widgets:
        if w.get("widgetType") != "COUPON_CARD_WIDGET":
            continue
        items = w.get("data", {}).get("items", {})
        heading = items.get("heading", {}).get("text", "")
        description = items.get("termsAndConditions", {}).get("description", "")
        coupon_code = items.get("couponCode", {}).get("text", "")
        status = items.get("couponButton", {}).get("state", "")
        subheading = items.get("subheading", {}).get("text", "")

        # Extract bank name from the offer title using parser
        bank = find_bank(heading) or "-"

        offers.append({
            "title": heading,
            "description": description,
            "bank": bank,
            "code": coupon_code,
            "status": status,
            "unlock": subheading,
        })
    return offers


def display_offers(offers):
    """Display offers in a rich table."""
    if not offers:
        console.print("[bold red][X] No offers found in the response.[/bold red]")
        return

    table = Table(
        title="[bold]Zepto Payment Offers[/bold]",
        border_style="bright_blue",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("Offer", style="white", max_width=45)
    table.add_column("Description", style="dim white", max_width=35)
    table.add_column("Bank", style="cyan", justify="center")
    table.add_column("Code", style="bold green", justify="center")
    table.add_column("Status", justify="center")

    for i, o in enumerate(offers, 1):
        status = o["status"]
        if status.lower() == "locked":
            status_fmt = f"[yellow]{status}[/yellow]"
        else:
            status_fmt = f"[green]{status}[/green]"

        desc = o["description"] or o["unlock"] or "-"

        table.add_row(
            str(i),
            o["title"],
            desc,
            o["bank"],
            o["code"] or "-",
            status_fmt,
        )

    console.print()
    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(offers)} offers found\n")


if __name__ == "__main__":
    data = fetch_raw()
    offers = parse_offers(data)

    # Save only relevant offer data
    Path("debug_response.json").write_text(
        json.dumps(offers, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    console.print(f"[dim]Saved {len(offers)} offers to debug_response.json[/dim]")

    display_offers(offers)