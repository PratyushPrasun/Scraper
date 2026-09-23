# Zepto Offers & Coupons Scraper (Scrap 2.0)

A Python-based utility to fetch, extract, and categorize live payment offers, bank discounts, and coupon codes from Zepto's BFF (Backend-For-Frontend) gateway API. To run this project, install dependencies via `pip install -r requirements.txt`, configure credentials using `python update_env.py` (paste your Zepto cURL from Chrome DevTools and press Enter twice), and run `python sd.py` to fetch offers and render the results table and `debug_response.json`.

> **⚡ Quick Start / How to Run:**
> ```bash
> pip install -r requirements.txt   # 1. Install dependencies
> python update_env.py              # 2. Paste Zepto cURL from DevTools & press Enter twice
> python sd.py                      # 3. Fetch offers & display results
> ```

---

## 📌 Features

- **Live Offer Extraction**: Queries Zepto's `/cfs/api/v1/cart/coupons/fetch-list` API endpoint for real-time coupon and payment offers tailored to your cart, store location, and coordinates.
- **Smart Bank & Network Identification**: Automatically detects bank entities (HDFC, ICICI, SBI, Axis, Kotak, IDFC, HSBC, Amex, etc.) and card networks (Visa, RuPay, Mastercard) using regex pattern matching.
- **Automated `.env` Setup via cURL**: Paste a cURL command straight from browser DevTools into `update_env.py`, which parses headers and JSON body parameters to update `.env` automatically.
- **Terminal UI**: Formats extracted deals into a clean, colored table powered by `rich`.
- **Structured Data Export**: Automatically saves parsed offers to `debug_response.json` for easy integration with downstream tools or data pipelines.
- **Session Expiry Alerts**: Detects expired tokens (HTTP 401) with actionable instructions on refreshing authentication.

---

## 🛠️ Tech Stack & Dependencies

### Language & Frameworks
- **Python 3.8+**

### Third-Party Libraries
- **[`requests`](https://requests.readthedocs.io/)** (`>= 2.31.0`): Sends authenticated HTTP POST requests with custom browser headers and payloads.
- **[`rich`](https://rich.readthedocs.io/)** (`>= 13.0.0`): Renders formatted terminal outputs, status tables, and colored text.
- **[`python-dotenv`](https://github.com/theskumar/python-dotenv)** (`>= 1.0.0`): Loads configuration and authentication credentials from the local `.env` file.

### Python Standard Libraries Used
- `re`: Regular expressions for pattern-matching bank names, discount amounts, promo codes, and unlock thresholds.
- `shlex`: Shell lexical analysis for robust parsing of bash, cmd, and powershell cURL syntax.
- `dataclasses`: Defines structured data representations for extracted `Offer` objects.
- `json`: Parsing and serializing API payloads and debug output files.
- `pathlib`: Cross-platform filesystem path management.

---

## 📂 Project Structure

```text
Scrap2.0/
├── .env                  # Environment variables with Zepto session credentials & location
├── .env.example          # Sample template for required environment variables
├── .gitignore            # Git exclusion rules (ignores secrets, cache, venv)
├── debug_response.json   # Parsed JSON output of offers from the latest run
├── parser.py             # Regex parser for bank names, discounts, promo codes, and offers
├── requirements.txt      # Python dependencies list
├── sd.py                 # Core scraper: fetches API data, parses offers, and prints table
├── update_env.py         # Helper script: parses a cURL command and writes credentials to .env
└── README.md             # Project documentation
```

### File Breakdown

| File | Purpose |
|------|---------|
| [**`sd.py`**](sd.py) | **Main entry point.** Reads `.env`, builds headers and payload, invokes the Zepto API, calls the parser, outputs a formatted Rich table in the terminal, and writes `debug_response.json`. |
| [**`update_env.py`**](update_env.py) | **Credential updater.** Reads a cURL command from standard input, parses headers (`cookie`, `request-signature`, `x-xsrf-token`, etc.) and body fields (`cartId`, `storeId`, coordinates), and updates `.env`. |
| [**`parser.py`**](parser.py) | **Parsing engine.** Contains bank keywords, card regexes, discount type detection (`percent`, `flat`, `cashback`), unlock amounts, and the `find_bank()` logic. |
| [**`debug_response.json`**](debug_response.json) | Output file containing clean, structured JSON with all extracted offers from the most recent run. |
| [**`.env`**](.env) | Secure storage for session cookies, request signatures, device IDs, cart ID, and coordinates (ignored by git). |
| [**`.env.example`**](.env.example) | Example environment file schema with empty placeholders. |
| [**`.gitignore`**](.gitignore) | Excludes `.env`, Python cache files (`__pycache__`), virtual environments, and generated debug output. |

---

## ⚙️ Prerequisites & Installation

### 1. Clone or Open the Directory
Open your terminal or command prompt in the project root:
```bash
cd "d:/Stack Projects/Scrap2.0"
```

### 2. (Optional) Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
Install the required packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Use

### Step 1: Capture cURL from Zepto

Zepto requires authenticated session cookies and request signatures to fetch coupons. You can obtain them directly from your browser:

1. Open [Zepto](https://www.zepto.com) in Google Chrome and log in.
2. Add at least one item to your cart and navigate to the **Cart / Checkout** page.
3. Open **Chrome Developer Tools** (`F12` or `Ctrl + Shift + I` / `Cmd + Option + I`).
4. Go to the **Network** tab.
5. In the filter box, type `fetch-list`.
6. Click on **Apply Coupon / View Offers** on the Zepto webpage to trigger the request.
7. Locate the request named `fetch-list` (URL: `.../cart/coupons/fetch-list`).
8. Right-click the request $\rightarrow$ **Copy** $\rightarrow$ **Copy as cURL (bash)** *(or Copy as cURL for Windows/PowerShell)*.

---

### Step 2: Update Credentials using `update_env.py`

Instead of manually editing the `.env` file, use `update_env.py` to automatically extract the tokens:

```bash
python update_env.py
```

1. You will see an interactive prompt:
   ```text
   Paste your cURL command below
     Right-click in Chrome DevTools -> Copy as cURL (bash)
     Then paste here and press Enter twice to confirm.
   ```
2. Paste the copied cURL command.
3. Press **Enter twice**.
4. The script will parse the headers and request body, update `.env`, and display a status table showing which keys were updated or newly added.

---

### Step 3: Run the Scraper (`sd.py`)

Execute the main script to fetch and display current payment offers:

```bash
python sd.py
```

#### What `sd.py` does:
1. Validates that all required environment variables exist in `.env`.
2. Sends an authenticated POST request to `https://bff-gateway.zepto.com/cfs/api/v1/cart/coupons/fetch-list`.
3. Filters for widgets of type `COUPON_CARD_WIDGET`.
4. Extracts bank names, promo codes, discount descriptions, unlock criteria, and current lock status.
5. Saves the parsed list to [**`debug_response.json`**](debug_response.json).
6. Displays a formatted table directly in your terminal.

---

## 📊 Terminal Output Preview

When running `python sd.py`, you will see output similar to this:

```text
[OK] All environment variables loaded.
>> Fetching coupons from Zepto...
[OK] Response received -- status 200
Saved 28 offers to debug_response.json

                               Zepto Payment Offers                               
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃  # ┃ Offer                                       ┃ Description              ┃  Bank  ┃ Code          ┃ Status ┃
┣━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━╋━━━━━━━━━━━━━━━╋━━━━━━━━┫
┃  1 ┃ Flat ₹1,500 Off with Axis Bank Credit Card. ┃ Valid on AirPods 5 Se... ┃  Axis  ┃ ZEPAIRAXIS    ┃ Locked ┃
┃  2 ┃ Flat ₹1,500 Off with SBI Credit Cards.      ┃ Valid on AirPods 5 Se... ┃  SBI   ┃ ZEPAIRSBIC    ┃ Locked ┃
┃  3 ┃ Flat ₹1,500 Off ICICI Bank Credit Card.     ┃ Valid on AirPods 5 Se... ┃ ICICI  ┃ ZEPAIRICICI   ┃ Locked ┃
┃  4 ┃ Flat ₹6,000 Off with Axis Bank Credit Card  ┃ Valid on iPhone 18 pro...┃  Axis  ┃ ZEPIPHONEAXIS ┃ Locked ┃
...
┗━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━┻━━━━━━━━━━━━━━━┻━━━━━━━━┛

Total: 28 offers found
```

---

## 📄 Output Data Format (`debug_response.json`)

The script saves offers in the following format:

```json
[
  {
    "title": "Flat ₹1,500 Off with Axis Bank Credit Card.",
    "description": "Valid on AirPods 5 Series products",
    "bank": "Axis",
    "code": "ZEPAIRAXIS",
    "status": "Locked",
    "unlock": "Shop for ₹5000 more to unlock"
  },
  {
    "title": "Flat ₹1,500 Off with SBI Credit Cards.",
    "description": "Valid on AirPods 5 Series products",
    "bank": "SBI",
    "code": "ZEPAIRSBIC",
    "status": "Locked",
    "unlock": "Shop for ₹5000 more to unlock"
  }
]
```

### JSON Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Primary headline describing the offer (e.g. discount and card criteria). |
| `description` | `string` | Terms and conditions or applicable product lines. |
| `bank` | `string` | Identified bank entity (e.g., `Axis`, `SBI`, `ICICI`) or card network (`RuPay`, `Visa`, `Mastercard`). |
| `code` | `string` | The promo code string to apply at checkout (e.g., `ZEPAIRAXIS`). |
| `status` | `string` | `Locked` (spend threshold not yet met) or `Unlocked`. |
| `unlock` | `string` | Spend requirement message if the offer is locked (e.g. "Shop for ₹5000 more to unlock"). |

---

## 🔑 Environment Variables Reference

The `.env` file requires the following variables:

| Variable | Description |
|----------|-------------|
| `ZEPTO_COOKIE` | Full session cookie string containing `accessToken`, `refreshToken`, and AWS WAF tokens. |
| `ZEPTO_CART_ID` | UUID of your active Zepto shopping cart. |
| `ZEPTO_STORE_ID` | Dark store UUID servicing your delivery address. |
| `ZEPTO_STORE_IDS` | Comma-separated store IDs (optional, falls back to `ZEPTO_STORE_ID`). |
| `ZEPTO_DEVICE_ID` | Client device identifier. |
| `ZEPTO_SESSION_ID` | User session identifier. |
| `ZEPTO_REQUEST_ID` | Request tracking UUID. |
| `ZEPTO_REQUEST_SIGNATURE`| Request verification signature computed by Zepto client scripts. |
| `ZEPTO_CSRF_SECRET` | CSRF secret token (`x-csrf-secret`). |
| `ZEPTO_XSRF_TOKEN` | XSRF validation token (`x-xsrf-token`). |
| `ZEPTO_WIDGET_ID` | Current layout widget identifier. |
| `ZEPTO_TIMEZONE_HEADER` | Timezone validation hash (`x-timezone`). |
| `ZEPTO_LAT` | User latitude coordinate (e.g. `12.96902`). |
| `ZEPTO_LON` | User longitude coordinate (e.g. `77.75395`). |

> **Note**: You do **not** need to assemble these manually. Simply run `python update_env.py` and paste the cURL from DevTools.

---

## ❓ Troubleshooting

### 1. `401 Unauthorized`
- **Cause**: Zepto's session tokens or `aws-waf-token` expire periodically.
- **Solution**: Open Zepto in your browser, refresh the cart page, copy a fresh cURL of `fetch-list`, and run `python update_env.py` to paste it.

### 2. `Missing from .env: ZEPTO_...`
- **Cause**: One or more required environment variables are absent from `.env`.
- **Solution**: Re-run `python update_env.py` with a complete cURL command from Chrome DevTools, or verify that `.env` contains all fields listed in the [Environment Variables Reference](#-environment-variables-reference).

### 3. Unicode / Encoding Issues on Windows Console
- Both `sd.py` and `update_env.py` configure standard output to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`) and force terminal mode with `rich`. If using a legacy `cmd.exe` terminal, switch to **Windows Terminal** or **PowerShell** for optimal rendering of rupee symbols (`₹`) and borders.
