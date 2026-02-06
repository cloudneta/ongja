import csv
import random
import string

def rand_digits(n: int) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))

def rand_name() -> str:
    last = random.choice(["Kim","Lee","Park","Choi","Jung","Kang","Cho","Yoon","Jang","Lim"])
    first = random.choice(["Minjun","Seoyeon","Jihun","Sumin","Jiwoo","Hyunwoo","Yuna","Hana","Junseo","Eunji"])
    return f"{first} {last}"

def rand_email(name: str) -> str:
    user = name.lower().replace(" ", ".")
    domain = random.choice(["example.com","example.net","corp.example","mail.test"])
    return f"{user}{random.randint(1,999)}@{domain}"

def rand_phone() -> str:
    return f"010-{rand_digits(4)}-{rand_digits(4)}"

def rand_rrn_like() -> str:
    if random.random() < 0.85:
        year = random.randint(70, 99)
        gender_code = random.choice(["1", "2"])
    else:
        year = random.randint(0, 9)
        gender_code = random.choice(["3", "4"])

    mm = random.randint(1, 12)
    dd = random.randint(1, 28)

    front = f"{year:02d}{mm:02d}{dd:02d}"
    rest = rand_digits(6)

    return f"{front}-{gender_code}{rest}"

def luhn_check_digit(number: str) -> str:
    digits = [int(d) for d in number]
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return str((10 - (checksum % 10)) % 10)

def rand_cc_like() -> str:
    prefix = random.choice(["4", "5"])
    base = prefix + rand_digits(14)
    check = luhn_check_digit(base)
    card = base + check
    return f"{card[0:4]}-{card[4:8]}-{card[8:12]}-{card[12:16]}"

def mask_rrn(rrn: str) -> str:
    return rrn[:8] + "******"

def mask_cc(cc: str) -> str:
    return cc[:5] + "****-****-" + cc[-4:]

def rand_address() -> str:
    city = random.choice(["Seoul","Busan","Incheon","Daegu","Daejeon","Gwangju"])
    street = random.choice(["Teheran-ro","Gangnam-daero","Sejong-daero","Centum-ro","Haeundae-ro"])
    return f"{city}, {street} {random.randint(1,200)}"

def gen_rows(n: int):
    rows = []
    for i in range(1, n+1):
        name = rand_name()
        rrn = rand_rrn_like()
        cc = rand_cc_like()
        rows.append({
            "customer_id": f"CUST-{i:04d}",
            "name": name,
            "email": rand_email(name),
            "phone": rand_phone(),
            "rrn_like": rrn,
            "credit_card_like": cc,
            "address": rand_address(),
            "memo": random.choice([
                "VIP customer",
                "Requested invoice email",
                "Address change requested",
                "Call back needed",
                "No special notes",
            ]),
        })
    return rows

def write_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def write_safe_csv(path: str, rows):
    safe = []
    for r in rows:
        r2 = dict(r)
        r2["rrn_like"] = mask_rrn(r2["rrn_like"])
        r2["credit_card_like"] = mask_cc(r2["credit_card_like"])
        safe.append(r2)
    write_csv(path, safe)

def rand_aws_access_key_id() -> str:
    return "AKIA" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

def rand_aws_secret_access_key() -> str:
    alphabet = string.ascii_letters + string.digits + "/+"
    return "".join(random.choice(alphabet) for _ in range(40))

def fake_openssh_private_key_block() -> str:
    b64 = string.ascii_letters + string.digits + "+/"
    prefix = "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQ"

    body_len = 1800 - len(prefix)
    body = prefix + "".join(random.choice(b64) for _ in range(body_len))

    body_lines = [body[i:i+64] for i in range(0, len(body), 64)]

    return "\n".join([
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        *body_lines,
        "-----END OPENSSH PRIVATE KEY-----",
    ])

def write_env(path: str, bucket_name: str):
    app = random.choice(["customer-api", "billing-api", "crm-api"])
    env = random.choice(["production", "staging"])
    db_user = random.choice(["app_user", "svc_customer", "svc_api"])
    db_pass = random.choice(["SuperSecretPassword!123", "P@ssw0rd!ChangeMe", "Welcome123!"])

    access_key = rand_aws_access_key_id()
    secret_key = rand_aws_secret_access_key()
    ssh_key = fake_openssh_private_key_block()

    content = f"""############################################################
# Application Environment Configuration
# (DO NOT COMMIT THIS FILE)
############################################################

# Application
APP_NAME={app}
APP_ENV={env}
APP_PORT=8080
LOG_LEVEL=INFO

# Database
DB_HOST=customer-db.internal
DB_PORT=5432
DB_NAME=customer
DB_USER={db_user}
DB_PASSWORD={db_pass}

# AWS Configuration
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID={access_key}
AWS_SECRET_ACCESS_KEY={secret_key}

# S3
S3_BUCKET={bucket_name}
S3_PREFIX=upload/

# External API
PAYMENT_API_ENDPOINT=https://api.payment.example.com
PAYMENT_API_KEY=pk_live_{rand_digits(20)}

# SSH Access (Legacy Bastion)
SSH_USER=ec2-user
SSH_HOST=bastion.internal

{ssh_key}

############################################################
# End of file
############################################################
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    random.seed()
    rows = gen_rows(60)
    write_csv("customer-data.csv", rows)
    write_safe_csv("customer-data-safe.csv", rows)

    # CNASG 버킷 네이밍 규칙 반영: cnasg-${NICKNAME}-customer-data
    nickname = "ongja"  # <- 필요하면 argparse로 받게 바꿔도 됨
    bucket = f"cnasg-{nickname}-customer-data"
    write_env("config.env", bucket)

    print("generated: customer-data.csv, customer-data-safe.csv, config.env")

if __name__ == "__main__":
    main()
