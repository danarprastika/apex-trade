$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = $ScriptDir
while ($Root -and -not (Test-Path (Join-Path $Root "docker-compose.yml"))) {
  $Root = Split-Path -Parent $Root
}
if (-not $Root) {
  throw "Unable to locate project root containing docker-compose.yml"
}

Write-Host "== Docker Compose config =="
Write-Host "Root: $Root"
Set-Location $Root
docker compose config | Out-Null

try {
  $dockerInfo = docker info 2>$null
  $dockerExitCode = $LASTEXITCODE
} catch {
  $dockerInfo = $null
  $dockerExitCode = 1
}
if ($dockerExitCode -eq 0) {
  Write-Host "== Docker daemon available; building backend and Telegram bot =="
  docker compose build backend telegram-bot
} else {
  Write-Host "== Docker daemon unavailable; running local validation fallback =="
  Write-Host "   - docker compose config: OK"
  Write-Host "   - backend tests: running"
  Set-Location (Join-Path $Root "backend")
  pytest -q
  Write-Host "   - Python compile: running"
  Set-Location $Root
  python -m compileall backend telegram-bot
  Write-Host "   - Alembic offline SQL: running"
  Set-Location (Join-Path $Root "backend")
  alembic upgrade head --sql | Out-Null
  Write-Host ""
  Write-Host "Validation completed without Docker daemon. Start Docker Desktop and run:"
  Write-Host "  docker compose build backend telegram-bot"
}
