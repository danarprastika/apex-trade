$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = $ScriptDir
while ($Root -and -not (Test-Path (Join-Path $Root "docker-compose.yml"))) {
  $Root = Split-Path -Parent $Root
}
if (-not $Root) {
  throw "Unable to locate project root containing docker-compose.yml"
}
Set-Location $Root

try {
  $dockerInfo = docker info 2>$null
  $dockerExitCode = $LASTEXITCODE
} catch {
  $dockerExitCode = 1
}

if ($dockerExitCode -ne 0) {
  Write-Host "Docker daemon is not available. Start Docker Desktop or run scripts\validate_local.ps1 for daemon-free validation."
  exit 1
}

docker compose up --build
