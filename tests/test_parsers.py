#!/usr/bin/env python3
"""Offline-Tests für Trim, EAN/GTIN-Validierung und Parser (spiegeln die Lambdas in barcode.yaml)."""

from __future__ import annotations


def trim_scan(raw: str) -> str:
    # wie find_first_not_of / find_last_not_of(" \t\r\n") in request_ean
    return raw.strip(" \t\r\n")


def parse_opengtindb(body: str) -> tuple[int, str, str]:
    error_code = -1
    name = ""
    detailname = ""
    vendor = ""
    start = 0
    text = body
    while start <= len(text):
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        line = text[start:end]
        if line.endswith("\r"):
            line = line[:-1]
        start = end + 1
        if not line or line == "---":
            if end == len(text):
                break
            continue
        eq = line.find("=")
        if eq == -1:
            if end == len(text):
                break
            continue
        key, value = line[:eq], line[eq + 1 :]
        if key == "error":
            error_code = int(value)
        elif key == "name" and not name:
            name = value
        elif key == "detailname" and not detailname:
            detailname = value
        elif key == "vendor" and not vendor:
            vendor = value
        if end == len(text):
            break
    product = detailname or name
    return error_code, product, vendor


def test_trim():
    assert trim_scan("40084060\r\n") == "40084060"
    assert trim_scan("\r40084060\n") == "40084060"
    assert trim_scan("40084060\r") == "40084060"
    assert trim_scan("  40084060  ") == "40084060"
    assert trim_scan("\n") == ""
    assert trim_scan("") == ""


def is_all_digits(s: str) -> bool:
    return bool(s) and all("0" <= c <= "9" for c in s)


def check_digit_ok(digits: str) -> bool:
    n = len(digits)
    if n not in (8, 12, 13, 14) or not is_all_digits(digits):
        return False
    # wie request_ean: Position von rechts ungerade -> Gewicht 3
    total = 0
    for i in range(n - 1):
        pos_from_right = n - 1 - i
        total += int(digits[i]) * (3 if pos_from_right % 2 else 1)
    check = (10 - (total % 10)) % 10
    return check == int(digits[-1])


def normalize_ean(raw: str) -> str | None:
    # Wie barcode_ean::normalize: nach Trim nur Ziffern, Länge 8/12/13/14, Prüfziffer korrekt.
    # Keine Ziffern aus gemischtem Müll extrahieren.
    s = trim_scan(raw)
    if not check_digit_ok(s):
        return None
    return s


def test_ean_valid_known():
    assert normalize_ean("4000417025005") == "4000417025005"
    assert normalize_ean("4006381333931") == "4006381333931"
    assert normalize_ean("4000417025005\r\n") == "4000417025005"
    assert normalize_ean("\r4006381333931\n") == "4006381333931"
    assert normalize_ean("  4000417025005  ") == "4000417025005"
    # EAN-8, UPC-A (12), GTIN-14
    assert normalize_ean("96385074") == "96385074"
    assert normalize_ean("012345678905") == "012345678905"
    assert normalize_ean("00012345678905") == "00012345678905"


def test_ean_invalid_garbage_and_check():
    assert normalize_ean("") is None
    assert normalize_ean("   ") is None
    assert normalize_ean("\n") is None
    assert normalize_ean("123") is None
    assert normalize_ean("4000417025006") is None  # falsche Prüfziffer
    assert normalize_ean("4006381333930") is None
    assert normalize_ean("abcdefg") is None
    assert normalize_ean("Error parse url") is None
    # typischer UART-Müll (nicht nur Ziffern) – nicht stillschweigend extrahieren
    assert normalize_ean("abc4000417025005def") is None
    assert normalize_ean("4000417 025005") is None
    assert normalize_ean("4000417025005\x00") is None
    assert normalize_ean("\x00\x01\x0a\xff") is None
    assert normalize_ean("Not connected to network") is None
    # Buchstaben/Binärreste dürfen nicht als Scan durchgehen
    raw = bytes([0x00, 0x1B, 0x0A, 0xFF, 0x30, 0x31]).decode("latin1")
    assert normalize_ean(raw) is None




def test_opengtindb_ok_docs_example():
    body = """error=0
---
name=Natürliches Mineralwasser
detailname=Bad Vilbeler RIED Quelle
vendor=H. Kroner GmbH & CO. KG
maincat=Getränke, Alkohol
subcat=
contents=19
---
"""
    error, product, vendor = parse_opengtindb(body)
    assert error == 0
    assert product == "Bad Vilbeler RIED Quelle"
    assert vendor == "H. Kroner GmbH & CO. KG"


def test_opengtindb_name_only_and_crlf():
    body = "error=0\r\nname=Testprodukt\r\nvendor=Firma GmbH\r\n"
    error, product, vendor = parse_opengtindb(body)
    assert error == 0
    assert product == "Testprodukt"
    assert vendor == "Firma GmbH"


def test_opengtindb_errors():
    assert parse_opengtindb("error=1\n")[0] == 1
    assert parse_opengtindb("error=5\n")[0] == 5
    assert parse_opengtindb("error=13\n")[0] == 13
    error, product, vendor = parse_opengtindb("error=5\nname=ShouldIgnore\nvendor=X\n")
    assert error == 5
    # Produkt wird bei error!=0 nicht verwendet; Parser liefert die Felder trotzdem
    assert product == "ShouldIgnore"


def test_opengtindb_field_order_not_fixed():
    body = "vendor=FirstVendor\nerror=0\ndetailname=\nname=OnlyName\n"
    error, product, vendor = parse_opengtindb(body)
    assert error == 0
    assert product == "OnlyName"
    assert vendor == "FirstVendor"



def parse_off_v3(body: dict) -> tuple[str, str] | None:
    """Wie barcode.yaml: status=success, Name deutsch > Hauptsprache > generic, erste Marke."""
    if body.get("status") != "success":
        return None
    product = body.get("product")
    if not isinstance(product, dict):
        return None
    name = ""
    for key in ("product_name_de", "product_name", "generic_name_de", "generic_name"):
        v = product.get(key) or ""
        if v:
            name = v
            break
    if not name:
        return None
    brands = product.get("brands") or ""
    return name, brands.split(",")[0]


def shopping_item(ean: str, product: str, brand: str) -> str:
    """Text für todo.add_item (wie Lambda in barcode.yaml)."""
    if not product:
        return ean
    if not brand or brand in product:
        return product
    return f"{brand} {product}"


def parse_eansuche(status_code: int, body: dict | None) -> tuple[str | None, str]:
    """200 + found + product_name = Treffer ohne Hersteller. 404/429 kein Name."""
    if status_code == 404:
        return None, "not_found"
    if status_code == 429:
        return None, "rate_limited"
    if status_code == 400:
        return None, "invalid_ean"
    if status_code != 200 or not body:
        return None, f"http_{status_code}"
    if not body.get("found"):
        return None, "not_found"
    name = body.get("product_name") or ""
    if not name:
        return None, "no_name"
    return name, "ok"


def test_off_v3_success():
    body = {
        "status": "success",
        "product": {
            "code": "4000417025005",
            "product_name": "Marzipan",
            "brands": "Ritter Sport",
            "product_type": "food",
        },
    }
    assert parse_off_v3(body) == ("Marzipan", "Ritter Sport")


def test_off_v3_success_without_brands():
    body = {"status": "success", "product": {"product_name": "Nur Name"}}
    assert parse_off_v3(body) == ("Nur Name", "")


def test_off_v3_rejects_failure_and_empty_name():
    assert parse_off_v3({"status": "failure", "product": {"product_name": "X"}}) is None
    assert parse_off_v3({"status": "success", "product": {}}) is None
    assert parse_off_v3({"status": "success", "product": {"product_name": ""}}) is None
    assert parse_off_v3({"status": "success", "product": {"product_name": None}}) is None
    # typischer Hinweis ohne Redirect: kein brauchbarer Name
    assert (
        parse_off_v3(
            {
                "status": "failure",
                "result": {"id": "product_found_with_a_different_product_type"},
            }
        )
        is None
    )


def test_off_v3_prefers_german_name():
    body = {
        "status": "success",
        "product": {
            "product_name_de": "Vollmilch-Schokolade",
            "product_name": "Milk chocolate",
            "generic_name": "Chocolate",
            "brands": "Ritter Sport, Alfred Ritter",
        },
    }
    assert parse_off_v3(body) == ("Vollmilch-Schokolade", "Ritter Sport")
    fallback = {"status": "success", "product": {"product_name_de": "", "product_name": "Crème", "brands": ""}}
    assert parse_off_v3(fallback) == ("Crème", "")
    generic = {"status": "success", "product": {"generic_name_de": "Hautcreme"}}
    assert parse_off_v3(generic) == ("Hautcreme", "")


def test_shopping_item_text():
    assert shopping_item("4000417025005", "Marzipan", "Ritter Sport") == "Ritter Sport Marzipan"
    assert shopping_item("4000417025005", "Ritter Sport - Marzipan", "Ritter Sport") == "Ritter Sport - Marzipan"
    assert shopping_item("4000417025005", "Marzipan", "") == "Marzipan"
    assert shopping_item("4005808262618", "", "") == "4005808262618"


def test_eansuche_success_no_brand():
    body = {
        "ok": True,
        "ean": "4000417025005",
        "found": True,
        "product_name": "Ritter Sport Ritter Sport - Marzipan",
        "country": "Deutschland",
    }
    name, reason = parse_eansuche(200, body)
    assert reason == "ok"
    assert name == "Ritter Sport Ritter Sport - Marzipan"


def test_eansuche_http_errors():
    not_found = {"ok": True, "ean": "4005808262618", "found": False, "product_name": None}
    assert parse_eansuche(404, not_found) == (None, "not_found")
    assert parse_eansuche(429, None) == (None, "rate_limited")
    assert parse_eansuche(400, {"found": False}) == (None, "invalid_ean")
    assert parse_eansuche(200, {"found": False, "product_name": None}) == (None, "not_found")
    assert parse_eansuche(200, {"found": True, "product_name": None}) == (None, "no_name")
    assert parse_eansuche(500, {})[0] is None


if __name__ == "__main__":
    tests = [
        test_trim,
        test_opengtindb_ok_docs_example,
        test_opengtindb_name_only_and_crlf,
        test_opengtindb_errors,
        test_opengtindb_field_order_not_fixed,
        test_off_v3_success,
        test_off_v3_success_without_brands,
        test_off_v3_rejects_failure_and_empty_name,
        test_off_v3_prefers_german_name,
        test_shopping_item_text,
        test_eansuche_success_no_brand,
        test_eansuche_http_errors,
        test_ean_valid_known,
        test_ean_invalid_garbage_and_check,
    ]
    for fn in tests:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(tests)} tests passed")
