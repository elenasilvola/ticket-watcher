# Asennus Windowsille

## 1. Esivaatimukset

- **Python 3.11+**: lataa [python.org/downloads](https://www.python.org/downloads/) -sivulta.
  Asennuksessa muista rastittaa **"Add python.exe to PATH"**.
- **Git**: lataa [git-scm.com/download/win](https://git-scm.com/download/win) (tai lataa repo
  GitHubista ZIP-tiedostona ilman gitia: vihreä "Code" -nappi → "Download ZIP").

## 2. Kloonaa repo ja asenna riippuvuudet

Avaa PowerShell ja aja:

```powershell
cd $HOME
git clone https://github.com/elenasilvola/ticket-watcher.git
cd ticket-watcher

python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\playwright install chromium
```

## 3. Luo .env-tiedosto

Samat tunnukset kelpaavat kuin Macilla (Gmailin App Password ei ole sidottu
laitteeseen). Aja PowerShellissa `ticket-watcher`-kansiosta:

```powershell
$pw = Read-Host "Gmail App Password (ilman valeja)" -AsSecureString
$plainPw = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw))

@"
EVENT_URL=https://www.ticketmaster.fi/event/melo-louna0nline-lippuja/1181155277
EVENT_LABEL=Melo, Louna0nline @ Allas Live (la 19.9.2026)
GMAIL_USER=elena.silvola@gmail.com
GMAIL_APP_PASSWORD=$plainPw
NOTIFY_EMAIL=elena.silvola@hotmail.fi
"@ | Out-File -Encoding utf8 .env

Remove-Variable plainPw, pw
```

## 4. Testaa kerran manuaalisesti

```powershell
.\venv\Scripts\python.exe check_tickets.py
```

Pitäisi tulostaa jotain kuten: `[Melo, ...] löydetty 0 lippua (edellinen tarkistus: 0).`

## 5. Asenna ajastus (Task Scheduler)

```powershell
.\windows\setup_task.ps1
```

Tämä rekisteröi ajastetun tehtävän "TicketWatcher", joka ajaa tarkistuksen
5 minuutin välein, myös taustalla ilman kirjautumista ulos. Voit tarkistaa
sen Task Scheduler -sovelluksesta (haku: "Task Scheduler" → Task Scheduler
Library → TicketWatcher).

**Huom:** kone ei saa olla horrostilassa (sleep) tarkistusten välissä —
sama rajoitus kuin Macilla. Asetuksissa `-AllowStartIfOnBatteries` on jo
päällä, mutta jos kone menee automaattisesti lepotilaan, tarkistukset
keskeytyvät siihen asti.

## Hallinta

```powershell
# Aja kerran heti
Start-ScheduledTask -TaskName TicketWatcher

# Poista ajastus kokonaan
Unregister-ScheduledTask -TaskName TicketWatcher -Confirm:$false

# Katso lokia (samaan state.json-tiedostoon tallennetaan tila)
Get-Content .\state.json
```

## Tärkeää, jos molemmat (Mac + Windows) ajavat samaan aikaan

Jos molemmat laitteet ovat **samassa kotiverkossa** (sama julkinen IP),
kannattaa käyttää vain toista kerrallaan — muuten sivua käydään
käytännössä joka 2,5 minuutti kahdelta koneelta, mikä nostaa riskiä
että Ticketmasterin bottisuojaus taas väliaikaisesti estää. Jos laitteet
ovat eri verkoissa (esim. Windows-kone eri paikassa), tämä ei ole ongelma.
