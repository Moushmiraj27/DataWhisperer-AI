$Restart = $args -contains "-Restart"
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".codex-venv\Scripts\python.exe"
$BackendUrl = "http://127.0.0.1:8000/api/v1/health"
$FrontendUrl = "http://127.0.0.1:8501"

if (-not (Test-Path $Python)) {
    Write-Host "Python environment not found: $Python" -ForegroundColor Red
    Write-Host "Create/install the environment first, then run this script again."
    exit 1
}

function Test-Url {
    param([string]$Url)

    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

Set-Location $Root

if ($Restart) {
    Write-Host "Restart requested. Stopping existing services on ports 8000 and 8501 ..." -ForegroundColor Cyan
    foreach ($Port in 8000, 8501) {
        Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique |
            ForEach-Object {
                if ($_ -and $_ -ne $PID) {
                    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
                }
            }
    }
    Start-Sleep -Seconds 2
}

if (Test-Url $BackendUrl) {
    Write-Host "Backend already running at http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "Starting backend at http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    Start-Process `
        -FilePath $Python `
        -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden

    $started = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Url $BackendUrl) {
            $started = $true
            break
        }
    }

    if (-not $started) {
        Write-Host "Backend did not start. Run the backend command manually to see the error." -ForegroundColor Red
        exit 1
    }

    Write-Host "Backend started." -ForegroundColor Green
}

if (Test-Url $FrontendUrl) {
    Write-Host "Frontend already running at $FrontendUrl" -ForegroundColor Green
    Start-Process $FrontendUrl
    exit 0
}

Write-Host "Starting frontend at $FrontendUrl ..." -ForegroundColor Cyan
Write-Host "Keep this window open while using DataWhisperer AI." -ForegroundColor Yellow

& $Python -m streamlit run frontend/app.py --server.headless=true --server.address=127.0.0.1 --server.port=8501
