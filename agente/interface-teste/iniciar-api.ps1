# Execute este script para iniciar a API no modo de testes com navegador.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$previousOrigins = $env:CORS_ORIGINS
Push-Location $projectRoot
try {
    $env:CORS_ORIGINS = 'http://127.0.0.1:5500,http://localhost:5500'
    & $pythonPath -m uvicorn app:app --host 127.0.0.1 --port 8000
} finally {
    $env:CORS_ORIGINS = $previousOrigins
    Pop-Location
}
