import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("SEZNAM_EMAIL")
PASSWORD = os.getenv("SEZNAM_PASSWORD")

# ===== moje veci co cchci mazat =====
SCHOOL_DOMAINS = ["@skola.cz", "@osu.cz", "@vsb.cz"]
JOB_KEYWORDS = ["práce", "pozice", "junior", "recruiter", "pohovor", "jobs.cz", "prace.cz", "linkedin"]
SPAM_KEYWORDS = ["sleva", "akce", "výprodej", "%", "promo", "newsletter", "dárek"]
SPAM_SENDERS = ["no-reply", "noreply", "newsletter", "marketing", "promo"]
LIMIT = 5
# =================================

#prevede to na text, kvuli bytum
def decode_mime(value):
    if not value:
        return ""
    parts = decode_header(value)
    text = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            text += part.decode(enc or "utf-8", errors="replace")
        else:
            text += part
    return text

def contains_any(text, words):
    t = text.lower()

    for w in words:
        if w.lower() in t:
            return True

    return False

def classify(sender, subject):
    s = sender.lower()
    sub = subject.lower()

    if contains_any(s, SCHOOL_DOMAINS):
        return "SCHOOL"
    if contains_any(s, JOB_KEYWORDS) or contains_any(sub, JOB_KEYWORDS):
        return "JOBS"
    if contains_any(s, SPAM_SENDERS) or contains_any(sub, SPAM_KEYWORDS):
        return "SPAM"

    return "OTHER"


print("Co chceš vypsat?")
print("1 - SPAM")
print("2 - PRÁCE")
print("3 - ŠKOLA")
print("4 - VŠE")

choice = input("Vyber (1-4): ").strip()

CATEGORY_MAP = {
    "1": "SPAM",
    "2": "JOBS",
    "3": "SCHOOL",
    "4": "ALL"
}

selected = CATEGORY_MAP.get(choice)
if not selected:
    print("Neplatná volba")
    exit()

# ====== IMAP ======
mail = imaplib.IMAP4_SSL("imap.seznam.cz", 993)
mail.login(EMAIL, PASSWORD)
mail.select("INBOX")

status, messages = mail.search(None, "ALL")
ids = messages[0].split()

print(f"\n--- Výpis: {selected} (max {LIMIT}) ---\n")

count = 0
to_delete = []


for msg_id in reversed(ids):
    if count >= LIMIT:
        break

    _, msg_data = mail.fetch(msg_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    sender = decode_mime(msg.get("From"))
    subject = decode_mime(msg.get("Subject"))

    category = classify(sender, subject)

    if selected != "ALL" and category != selected:
        continue

    count += 1
    print(f"{count}. [{category}]")
    print(f"   Od: {sender}")
    print(f"   Předmět: {subject}")
    print("-" * 50)

    to_delete.append(msg_id)

if to_delete:
    potvrdit  = input(f"\nChceš smazat {len(to_delete)} vypsaných emailů? napiš SMAZAT: ").strip()
    if potvrdit  == "SMAZAT":
        for msg_id in to_delete:
            mail.store(msg_id, "+FLAGS", r"(\Deleted)")
        mail.expunge()
        print("uspesne smazano ")



mail.logout()

print(f"\n✅ Vypsáno {count} e-mailů.")
