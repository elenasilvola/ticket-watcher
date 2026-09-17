# ticket-watcher

Tarkistaa automaattisesti Ticketmaster-tapahtuman "Vahvistetut jälleenmyyntiliput"
(resale) -osion ja lähettää sähköposti-ilmoituksen heti kun uusia lippuja
ilmestyy myyntiin.

**Käytössä oleva ajotapa: tämä Mac, `launchd`-ajastuksella, 5 min välein.**
(GitHub Actions -vaihtoehto kokeiltiin, mutta Ticketmasterin bottisuojaus
estää sen pilvipalvelin-IP:t suoraan — ks. "Miksi ei GitHub Actions" alla.)

Windows-koneelle asennusohjeet: [windows/README.md](windows/README.md).

## Miten se toimii

- `check_tickets.py` avaa tapahtumasivun Playwrightilla (headless Chromium)
  ja `playwright-stealth`-kirjastolla, joka piilottaa tyypilliset
  automaatiotunnisteet (mm. `navigator.webdriver`).
- Skripti vertaa löydettyjen lippujen määrää edelliseen tarkistukseen
  (`state.json`). Jos määrä kasvaa, lähetetään sähköposti Gmailin SMTP:n
  kautta osoitteesta `elena.silvola@gmail.com` vastaanottajalle
  `elena.silvola@hotmail.fi`.
- macOS:n `launchd`-palvelu (`com.elenasilvola.ticketwatcher.plist`,
  asennettu `~/Library/LaunchAgents/`-kansioon) käynnistää skriptin
  automaattisesti 5 minuutin välein, myös uudelleenkäynnistyksen jälkeen.

## Tila ja hallinta

```bash
# Onko ajastus käynnissä?
launchctl list | grep ticketwatcher

# Viimeisimmät lokirivit
tail -f ~/ticket-watcher/logs/ticket-watcher.log

# Pysäytä ajastus kokonaan
launchctl bootout gui/$(id -u)/com.elenasilvola.ticketwatcher

# Käynnistä uudelleen
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.elenasilvola.ticketwatcher.plist

# Aja kerran heti (ei odota seuraavaa ajastettua hetkeä)
launchctl kickstart -k gui/$(id -u)/com.elenasilvola.ticketwatcher
```

## Asetusten muuttaminen

Asetukset ovat `~/ticket-watcher/.env`-tiedostossa (ei gitissä):

```
EVENT_URL=...          # tapahtuman Ticketmaster-osoite
EVENT_LABEL=...         # nimi joka näkyy sähköpostin otsikossa
GMAIL_USER=...           # lähettäjän Gmail-osoite
GMAIL_APP_PASSWORD=...  # Gmailin sovelluskohtainen salasana (16 merkkiä, ei välejä)
NOTIFY_EMAIL=...         # vastaanottajan sähköposti
```

Tarkistusvälin muuttaminen: muokkaa `StartInterval`-arvoa (sekunteina)
tiedostossa `~/Library/LaunchAgents/com.elenasilvola.ticketwatcher.plist`,
tallenna, ja aja `launchctl bootout` + `launchctl bootstrap` uudelleen.

## Miksi ei GitHub Actions

Kokeilimme ensin GitHub Actionsia (ilmainen, ei vaadi omaa konetta päällä),
mutta Ticketmasterin bottisuojaus (todennäköisesti PerimeterX/HUMAN Security)
esti GitHub Actionsin pilvipalvelin-IP:n suoraan sivulla
"Your Browsing Activity Has Been Paused". Tämä ei liity meidän koodiin —
kyse on IP-maineeseen perustuvasta estosta, jota ei voi kiertää.
Workflow (`.github/workflows/check-tickets.yml`) on jätetty repoon mutta
poistettu käytöstä (`gh workflow disable`).

## Tärkeitä huomioita

- **Botintunnistus on herkkä myös kotiverkosta:** testauksen aikana myös
  tämä kone sai hetkellisen eston toistuvien nopeiden testiajojen jälkeen.
  Korjasimme tämän `playwright-stealth`-kirjastolla ja nostamalla
  tarkistusväliä 2 minuutista 5 minuuttiin. Jos esto ("Your Browsing
  Activity Has Been Paused" -teksti lokissa) ilmestyy uudelleen, harkitse
  tarkistusvälin kasvattamista edelleen (esim. 10-15 min).
- **Mac pitää olla päällä/verkossa** tarkistusten välissä. Jos kone on
  sammuksissa jonkin ajan, tarkistukset jatkuvat automaattisesti heti kun
  kirjaudut takaisin sisään.
- Skripti ei osta eikä varaa lippuja mitenkään — se vain lukee sivun ja
  lähettää ilmoituksen. Ostaminen jää sinulle, ja resell-liput voivat
  myydä loppuun nopeasti, joten ilmoituksen jälkeen kannattaa toimia heti.

## Paikallinen testaus

```bash
cd ~/ticket-watcher
source venv/bin/activate
python3 check_tickets.py
```

`HEADLESS=false python3 check_tickets.py` avaa näkyvän selainikkunan,
jos haluat nähdä mitä skripti oikeasti tekee.
