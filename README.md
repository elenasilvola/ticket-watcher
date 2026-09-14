# ticket-watcher

Tarkistaa automaattisesti Ticketmaster-tapahtuman "Vahvistetut jälleenmyyntiliput"
(resale) -osion ja lähettää sähköposti-ilmoituksen heti kun uusia lippuja
ilmestyy myyntiin. Ajetaan GitHub Actionsissa n. 5 minuutin välein, täysin ilmaiseksi.

## Miten se toimii

- `check_tickets.py` avaa tapahtumasivun oikealla (headless) selaimella
  Playwrightilla — pelkkä HTTP-haku ei toimi, koska Ticketmasterilla on
  botintunnistushaaste ennen sivun latautumista.
- Skripti vertaa löydettyjen lippujen määrää edelliseen tarkistukseen
  (`state.json`). Jos määrä kasvaa, lähetetään sähköposti Gmailin SMTP:n kautta.
- GitHub Actions -workflow (`.github/workflows/check-tickets.yml`) ajaa
  skriptin cron-ajastuksella ja committaa päivittyneen `state.json`:n
  takaisin repoon, jotta tila säilyy ajojen välillä.

## Käyttöönotto

### 1. Luo Gmailin sovelluskohtainen salasana

Tätä käytetään vain sähköpostin lähettämiseen (osoitteesta
`elena.silvola@gmail.com`), ei kirjautumiseen mihinkään.

1. Varmista että Google-tilillä on 2-vaiheinen vahvistus päällä.
2. Mene osoitteeseen https://myaccount.google.com/apppasswords
3. Luo uusi sovelluskohtainen salasana (nimeksi esim. "ticket-watcher").
4. Kopioi 16-merkkinen salasana talteen — sitä ei näytetä enää uudelleen.

### 2. Luo GitHub-repo ja työnnä koodi

Repo pitää olla **julkinen**, jotta GitHub Actions -ajot ovat ilmaisia
rajattomasti (yksityisessä revossa ilmainen kiintiö loppuisi nopeasti
5 min välein ajettavalta selainautomaatiolta). Salasanat pysyvät silti
suojattuina GitHub Secretsissä — ne eivät näy kenellekään, eivät edes
työkirjan lokeissa.

Pyydä minua ajamaan tämä, tai aja itse:

```bash
cd ~/ticket-watcher
git init -b main
git add .
git commit -m "Alusta ticket-watcher"
gh auth login
gh repo create ticket-watcher --public --source=. --remote=origin --push
```

### 3. Lisää salaisuudet (Secrets) ja asetukset (Variables)

```bash
gh secret set GMAIL_USER --body "elena.silvola@gmail.com"
gh secret set GMAIL_APP_PASSWORD   # liitä 16-merkkinen sovellussalasana kehotteeseen
gh secret set NOTIFY_EMAIL --body "elena.silvola@hotmail.fi"

gh variable set EVENT_URL --body "https://www.ticketmaster.fi/event/melo-louna0nline-lippuja/1181155277"
gh variable set EVENT_LABEL --body "Melo, Louna0nline @ Allas Live"
```

Tai GitHubin verkkosivulla: repo → **Settings → Secrets and variables → Actions**.

### 4. Testaa manuaalisesti

```bash
gh workflow run check-tickets.yml
gh run watch
```

Tai GitHubin sivulla: **Actions**-välilehti → *Tarkista jalleenmyyntiliput* → **Run workflow**.

Jos kaikki toimii, ajastettu tarkistus alkaa pyöriä itsestään ~5 min välein.

## Tärkeitä huomioita

- **Cloud-IP-riski:** GitHub Actions ajaa pilvipalvelimelta (ei kotisi
  IP-osoitteesta). Testasin botintunnistuksen läpäisyn tällä koneella
  onnistuneesti, mutta Ticketmasterin suojaus saattaa kohdella
  datakeskus-IP:tä eri tavalla. Jos ajo alkaa toistuvasti epäonnistua
  (`Actions`-välilehdellä näkyy punaisia ajoja), kerro minulle — voin
  rakentaa vaihtoehdon, joka ajaa tarkistuksen tällä Macilla `launchd`:n
  kautta (kotisi IP:stä, ei tätä riskiä).
- **Ajastuksen tarkkuus:** GitHub Actionsin cron ei ole täsmällinen —
  ajo voi joskus myöhästyä muutamalla minuutilla ruuhka-aikoina.
- **60 päivän inaktiivisuussääntö:** GitHub sammuttaa ajastetut workflow't
  jos repoon ei tule yhtään committia 60 päivään. Tämän pitäisi ratketa
  itsestään, koska workflow committaa `state.json`:n joka ajolla.
- Skripti ei osta eikä varaa lippuja mitenkään — se vain lukee sivun ja
  lähettää ilmoituksen. Ostaminen jää sinulle, ja resell-liput voivat
  myydä loppuun nopeasti, joten ilmoituksen jälkeen kannattaa toimia heti.

## Paikallinen testaus

```bash
cd ~/ticket-watcher
source venv/bin/activate
export EVENT_URL="https://www.ticketmaster.fi/event/melo-louna0nline-lippuja/1181155277"
export EVENT_LABEL="Melo testi"
export GMAIL_USER="elena.silvola@gmail.com"
export GMAIL_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export NOTIFY_EMAIL="elena.silvola@hotmail.fi"
python3 check_tickets.py
```
