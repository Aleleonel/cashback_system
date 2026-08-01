param(
    [Parameter(Mandatory)]
    [string]$DiretorioBackup,

    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $ProjectRoot "scripts\lib\Projeto.Backup.psm1") -Force

Set-Location -LiteralPath $ProjectRoot
Restore-ProjetoBackup -DiretorioBackup $DiretorioBackup

Write-Host "Rollback concluido."
