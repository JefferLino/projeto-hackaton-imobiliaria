# Inicia a interface e o receptor de lembretes no mesmo servidor.
$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $agentRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Ambiente .venv nao encontrado na pasta agente.'
}
$probe = New-Object System.Net.Sockets.TcpClient
try {
    $probe.Connect('127.0.0.1', 5500)
    $portBusy = $true
} catch {
    $portBusy = $false
} finally {
    $probe.Dispose()
}
if ($portBusy) {
    throw 'Porta 5500 ocupada. Pare o servidor antigo com Ctrl+C no terminal dele e execute este script novamente.'
}
Push-Location $agentRoot
try {
    Write-Host 'Chat: http://127.0.0.1:5500/'
    Write-Host 'Lembretes: http://127.0.0.1:5500/lembretes'
    & $pythonPath -m uvicorn receiver:app --app-dir $PSScriptRoot --host 127.0.0.1 --port 5500
} finally {
    Pop-Location
}
