$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\manage.py")) {
    throw "Coloque este script na raiz do projeto, ao lado do manage.py."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = ".\temp_chatgpt\backup_erro_ui_$timestamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null

Write-Host "Salvando o estado parcial em $backup..." -ForegroundColor Yellow

if (Test-Path ".\templates") {
    Copy-Item ".\templates" (Join-Path $backup "templates") -Recurse -Force
}

if (Test-Path ".\static\ui") {
    Copy-Item ".\static\ui" (Join-Path $backup "static_ui") -Recurse -Force
}

Write-Host "Restaurando arquivos rastreados pelo Git..." -ForegroundColor Cyan

$trackedTemplates = @(
    ".\templates\base.html",
    ".\templates\partials\sidebar.html",
    ".\templates\partials\navbar.html"
)

foreach ($file in $trackedTemplates) {
    git restore --source=HEAD -- $file

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao restaurar $file pelo Git."
    }
}

Write-Host "Removendo arquivos incompletos da tentativa anterior..." -ForegroundColor Cyan

if (Test-Path ".\static\ui") {
    Remove-Item ".\static\ui" -Recurse -Force
}

$messagesPath = ".\templates\partials\messages.html"

$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

git ls-files --error-unmatch -- $messagesPath *> $null
$messagesTracked = ($LASTEXITCODE -eq 0)

$ErrorActionPreference = $previousErrorPreference

if ((Test-Path $messagesPath) -and -not $messagesTracked) {
    Remove-Item $messagesPath -Force
}

$badScript = ".\aplicar_ui_foundation_01.ps1"

if (Test-Path $badScript) {
    Move-Item `
        $badScript `
        (Join-Path $backup "aplicar_ui_foundation_01_com_erro.ps1") `
        -Force
}

Write-Host "Executando validação..." -ForegroundColor Cyan

$check = python manage.py check 2>&1
$exitCode = $LASTEXITCODE

$check | ForEach-Object {
    Write-Host $_
}

$report = @"
=== DATA ===
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

=== BRANCH ===
$(git branch --show-current)

=== GIT STATUS ===
$(git status --short)

=== DJANGO CHECK ===
$($check | Out-String)

=== BACKUP ===
$backup
"@

Set-Content `
    -Path ".\diagnostico_recuperacao_ui.txt" `
    -Value $report `
    -Encoding UTF8

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "A recuperação terminou, mas o Django check encontrou erro." -ForegroundColor Red
    Write-Host "Anexe diagnostico_recuperacao_ui.txt." -ForegroundColor Yellow
    exit $exitCode
}

Write-Host ""
Write-Host "Projeto recuperado com sucesso." -ForegroundColor Green
Write-Host "Relatório: .\diagnostico_recuperacao_ui.txt" -ForegroundColor Yellow
Write-Host "Backup: $backup" -ForegroundColor Yellow
