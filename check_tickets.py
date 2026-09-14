#!/usr/bin/env python3
"""
Tarkistaa Ticketmaster-tapahtumasivun "Vahvistetut jalleenmyyntiliput"
(resale) -osion ja lahettaa sahkopostin, kun uusia lippuja ilmestyy myyntiin.

Ymparistomuuttujat (ks. .env.example):
  EVENT_URL          Tapahtuman Ticketmaster-osoite
  EVENT_LABEL         Vapaavalintainen nimi ilmoituksia varten
  GMAIL_USER           Lahettajan Gmail-osoite
  GMAIL_APP_PASSWORD  Gmailin sovelluskohtainen salasana
  NOTIFY_EMAIL         Vastaanottajan sahkopostiosoite (voi olla eri palvelu, esim. hotmail)
  STATE_FILE          Polku tila-tiedostoon (oletus: state.json)
"""
import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

from playwright.sync_api import sync_playwright

RESALE_HEADING = "Vahvistetut jälleenmyyntiliput"
RESALE_MARKER = "Vahvistettu jälleenmyyntilippu"
SECTION_END_MARKER = "Me ja kumppanimme käsittelemme tietojasi"
LISTING_RE = re.compile(
    r"Vahvistettu jälleenmyyntilippu\s*\n(\d+)\s+saatavilla\s*\n(.+?)\s*\n([\d.,]+)\s*€",
    re.MULTILINE,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def fetch_resale_section(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT, locale="fi-FI")
        page.goto(url, wait_until="networkidle", timeout=45000)
        try:
            page.wait_for_selector(f"text={RESALE_HEADING}", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(1200)
        body_text = page.inner_text("body")
        page_title = page.title()
        page_url = page.url
        browser.close()

    idx = body_text.find(RESALE_HEADING)
    if idx == -1:
        print(f"[debug] page.title() = {page_title!r}")
        print(f"[debug] page.url = {page_url!r}")
        print(f"[debug] body_text[:1500] = {body_text[:1500]!r}")
        raise RuntimeError("Resale-osiota ei löytynyt sivulta - sivun rakenne on ehkä muuttunut.")
    end_idx = body_text.find(SECTION_END_MARKER, idx)
    if end_idx == -1:
        end_idx = idx + 3000
    return body_text[idx:end_idx]


def parse_listings(section: str) -> list[dict]:
    listings = []
    for qty, name, price in LISTING_RE.findall(section):
        listings.append({"qty": int(qty), "name": name.strip(), "price": price.strip()})
    if not listings and RESALE_MARKER in section:
        # Tunnistettu lippu, mutta rakenteen jäsennys ei osunut - ilmoita silti.
        listings.append({"qty": 1, "name": "Tuntematon lipputyyppi (tarkista sivulta)", "price": "?"})
    return listings


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"total_qty": 0}


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def send_email(subject: str, body: str) -> None:
    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_APP_PASSWORD"]
    notify_email = os.environ["NOTIFY_EMAIL"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = notify_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, [notify_email], msg.as_string())


def main() -> int:
    event_url = os.environ["EVENT_URL"]
    event_label = os.environ.get("EVENT_LABEL", event_url)
    state_path = Path(os.environ.get("STATE_FILE", "state.json"))

    section = fetch_resale_section(event_url)
    listings = parse_listings(section)
    total_qty = sum(item["qty"] for item in listings)

    state = load_state(state_path)
    previous_qty = state.get("total_qty", 0)

    print(f"[{event_label}] löydetty {total_qty} lippua (edellinen tarkistus: {previous_qty}).")

    if total_qty > previous_qty:
        lines = [f"Uusia jalleenmyyntilippuja saatavilla tapahtumaan: {event_label}", "", event_url, ""]
        for item in listings:
            lines.append(f"- {item['qty']} kpl: {item['name']} ({item['price']} €)")
        body = "\n".join(lines)
        send_email(f"Lippuja saatavilla: {event_label}", body)
        print("Sähköposti-ilmoitus lähetetty.")

    save_state(state_path, {"total_qty": total_qty})
    return 0


if __name__ == "__main__":
    sys.exit(main())
