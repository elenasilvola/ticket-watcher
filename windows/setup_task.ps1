# Asentaa ticket-watcherin Windowsin Task Scheduleriin.
# Aja tama PowerShellista ticket-watcher-kansion sisalta (repo juuri), esim:
#   cd C:\Users\<kayttaja>\ticket-watcher
#   .\windows\setup_task.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$PythonExe = Join-Path $RepoRoot "venv\Scripts\pythonw.exe"
$ScriptPath = Join-Path $RepoRoot "check_tickets.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Ei loytynyt: $PythonExe`nAja ensin: python -m venv venv; .\venv\Scripts\pip install -r requirements.txt; .\venv\Scripts\playwright install chromium"
    exit 1
}

if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    Write-Error "Ei loytynyt .env-tiedostoa. Luo se ensin (ks. README) ennen ajastuksen kayttoonottoa."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $RepoRoot

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 3)

Register-ScheduledTask -TaskName "TicketWatcher" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Tarkistaa Ticketmaster resale-liput 5 min valein ja lahettaa sahkopostin" `
    -Force

Write-Host "Ajastus 'TicketWatcher' asennettu. Tarkista Task Scheduler -sovelluksesta (Task Scheduler Library)."
Write-Host "Voit kaynnistaa sen heti testiksi: Start-ScheduledTask -TaskName TicketWatcher"
