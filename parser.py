import re
from dataclasses import dataclass, asdict
from typing import Optional

# Bank/network keywords that mark an offer as bank/card-specific.
BANKS = [
    "HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "IDFC", "HSBC", "YES BANK",
    "PUNJAB NATIONAL BANK", "PNB", "BOB", "BANK OF BARODA", "CANARA",
    "INDUSIND", "RBL", "FEDERAL", "AMEX", "AMERICAN EXPRESS", "AU SMALL FINANCE",
    "AU SMALL", "AU", "STANDARD CHARTERED", "CITI", "UNION BANK", "IDBI",
    "DBS", "INDIAN OVERSEAS BANK", "IOB", "INDIAN BANK", "JANA", "NOVIO",
]
CARD_WORDS = re.compile(r"\b(credit|debit)\s+cards?\b", re.I)
# Things we explicitly do NOT want, unless a bank is also named.
NON_CARD = re.compile(r"amazon pay|paytm|phonepe|mobikwik|wallet|zepto pass|delivery", re.I)

TITLE_RE = re.compile(r"(?i)\b(flat|get|upto|up to|save)\b.*\b(off|cashback)\b")
PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
RUPEE_RE = re.compile(r"₹\s?(\d[\d,]*)")
CODE_RE = re.compile(r"\bZEP[A-Z0-9]{2,}\b")
UNLOCK_RE = re.compile(r"shop for\s*₹\s?(\d[\d,]*)\s*more to unlock", re.I)


@dataclass
class Offer:
    title: str
    bank: Optional[str]
    card_type: Optional[str]
    discount_type: str            # "percent" | "flat" | "cashback" | "unknown"
    discount_value: Optional[float]
    max_discount: Optional[float]
    promo_code: Optional[str]
    amount_to_unlock: Optional[float]   # extra spend still needed (cart-dependent)
    status: str                   # "locked" | "unlocked"


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def find_bank(text: str) -> Optional[str]:
    up = text.upper()
    for b in BANKS:
        if re.search(rf"\b{re.escape(b)}\b", up):
            return b.title() if b not in ("HDFC", "ICICI", "SBI", "PNB", "HSBC", "IDFC", "RBL", "BOB", "IDBI", "DBS", "IOB", "AU") else b
    # Check for card network if no specific bank is named
    for net in ("VISA", "RUPAY", "MASTERCARD"):
        if re.search(rf"\b{re.escape(net)}\b", up):
            return "RuPay" if net == "RUPAY" else net.title()
    return None


def is_bank_or_card_offer(text: str) -> bool:
    if find_bank(text):
        return True
    # No bank named: accept only if it says credit/debit card and isn't a wallet etc.
    return bool(CARD_WORDS.search(text)) and not NON_CARD.search(text)


def parse_offer(chunk: str) -> Optional[Offer]:
    lines = [l.strip() for l in chunk.splitlines() if l.strip()]
    title = next((l for l in lines if TITLE_RE.search(l)), None)
    if not title or not is_bank_or_card_offer(title):
        return None

    card = CARD_WORDS.search(title)
    card_type = card.group(1).lower() if card else None
    if re.search(r"mastercard|visa|rupay", title, re.I) and not card_type:
        card_type = "card"

    pct = PERCENT_RE.search(title)
    rupees = [_num(r) for r in RUPEE_RE.findall(title)]
    is_cashback = "cashback" in title.lower()

    if pct:
        dtype, dval = "percent", _num(pct.group(1))
        cap = rupees[0] if rupees else None          # "15% up to ₹125"
    elif rupees:
        dtype, dval, cap = ("cashback" if is_cashback else "flat"), rupees[0], None
    else:
        dtype, dval, cap = "unknown", None, None

    unlock = UNLOCK_RE.search(chunk)
    code = CODE_RE.search(chunk)
    return Offer(
        title=title,
        bank=find_bank(title),
        card_type=card_type,
        discount_type=dtype,
        discount_value=dval,
        max_discount=cap,
        promo_code=code.group(0) if code else None,
        amount_to_unlock=_num(unlock.group(1)) if unlock else None,
        status="locked" if (unlock and _num(unlock.group(1)) > 0) else "unlocked",
    )


def parse_panel_text(panel_text: str) -> list[dict]:
    """Each offer card ends with a 'Know more' link, so split on it."""
    offers, seen = [], set()
    for chunk in re.split(r"know more", panel_text, flags=re.I):
        o = parse_offer(chunk)
        if o and (o.promo_code or o.title) not in seen:
            seen.add(o.promo_code or o.title)
            offers.append(asdict(o))
    return offers