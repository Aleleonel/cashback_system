$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " CASHBACK SYSTEM - UI-01A" -ForegroundColor Cyan
Write-Host " CRIACAO SEGURA DA BASE VISUAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\manage.py")) {
    throw "Execute este script na raiz do projeto, ao lado do manage.py."
}

$branch = git branch --show-current

if ($branch -ne "feature/ui-foundation") {
    throw "Branch atual: $branch. Para evitar regressao, execute na branch feature/ui-foundation."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = ".\temp_chatgpt\backup_ui_01a_$timestamp"
$utf8SemBom = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $fullPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
    $directory = Split-Path -Parent $fullPath

    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    [System.IO.File]::WriteAllText($fullPath, $Content, $utf8SemBom)
}

Write-Host "Verificando estado atual do projeto..." -ForegroundColor Cyan

$initialStatus = git status --short

if ($initialStatus) {
    $allowedFiles = @(
        "recuperar_tentativa_ui.ps1",
        "recuperar_tentativa_ui_v2.ps1",
        "diagnostico_recuperacao_ui.txt",
        "aplicar_ui_01a_seguro.ps1",
        "aplicar_ui_01a_seguro_v2.ps1"
    )

    $unexpectedChanges = @()

    foreach ($line in $initialStatus) {
        $path = $line.Substring(3).Trim()

        if ($allowedFiles -notcontains $path) {
            $unexpectedChanges += $line
        }
    }

    if ($unexpectedChanges.Count -gt 0) {
        Write-Host ""
        Write-Host "Foram encontradas alteracoes nao esperadas:" -ForegroundColor Red
        $unexpectedChanges | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        throw "A etapa foi interrompida para evitar sobrescrever trabalho existente."
    }
}

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

if (Test-Path ".\static\ui") {
    Write-Host "Criando backup da pasta static/ui existente..." -ForegroundColor Yellow
    Copy-Item ".\static\ui" (Join-Path $backupDir "ui") -Recurse -Force
}

Write-Host "Criando estrutura static/ui..." -ForegroundColor Cyan

@(
    ".\static\ui\css",
    ".\static\ui\js"
) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

Write-Utf8File ".\static\ui\css\tokens.css" @'
:root {
    --ui-primary: #2563eb;
    --ui-primary-hover: #1d4ed8;
    --ui-primary-soft: #eff6ff;

    --ui-success: #16a34a;
    --ui-warning: #d97706;
    --ui-danger: #dc2626;
    --ui-info: #0891b2;

    --ui-body-bg: #f4f7fb;
    --ui-surface: #ffffff;
    --ui-surface-muted: #f8fafc;

    --ui-heading: #0f172a;
    --ui-text: #172033;
    --ui-text-muted: #64748b;

    --ui-border: #e2e8f0;
    --ui-border-strong: #cbd5e1;

    --ui-radius-sm: 0.375rem;
    --ui-radius-md: 0.625rem;
    --ui-radius-lg: 0.875rem;
    --ui-radius-xl: 1.125rem;

    --ui-shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
    --ui-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
    --ui-shadow-lg: 0 18px 45px rgba(15, 23, 42, 0.12);

    --ui-sidebar-width: 280px;
    --ui-navbar-height: 72px;

    --ui-transition-fast: 150ms ease;
    --ui-transition-normal: 220ms ease;
}
'@

Write-Utf8File ".\static\ui\css\base.css" @'
html,
body {
    min-height: 100%;
}

body {
    margin: 0;
    background: var(--ui-body-bg);
    color: var(--ui-text);
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    font-size: 0.9375rem;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

a {
    text-decoration: none;
}

h1,
h2,
h3,
h4,
h5,
h6 {
    color: var(--ui-heading);
    letter-spacing: -0.015em;
}

.text-muted {
    color: var(--ui-text-muted) !important;
}

:focus-visible {
    outline: 3px solid rgba(37, 99, 235, 0.25);
    outline-offset: 2px;
}

::selection {
    background: rgba(37, 99, 235, 0.18);
}
'@

Write-Utf8File ".\static\ui\css\components.css" @'
.card {
    border-color: var(--ui-border);
    border-radius: var(--ui-radius-lg);
    box-shadow: var(--ui-shadow-sm);
}

.card-header,
.card-footer {
    background: var(--ui-surface);
    border-color: var(--ui-border);
}

.btn {
    border-radius: var(--ui-radius-md);
    font-weight: 600;
}

.btn-primary {
    background: var(--ui-primary);
    border-color: var(--ui-primary);
}

.btn-primary:hover,
.btn-primary:focus {
    background: var(--ui-primary-hover);
    border-color: var(--ui-primary-hover);
}

.alert {
    border-radius: var(--ui-radius-lg);
}

.dropdown-menu {
    border-color: var(--ui-border);
    border-radius: var(--ui-radius-lg);
    box-shadow: var(--ui-shadow-md);
}

.badge {
    font-weight: 600;
}
'@

Write-Utf8File ".\static\ui\css\forms.css" @'
.form-label {
    margin-bottom: 0.375rem;
    color: var(--ui-heading);
    font-size: 0.8125rem;
    font-weight: 600;
}

.form-control,
.form-select {
    min-height: 42px;
    color: var(--ui-text);
    background-color: var(--ui-surface);
    border-color: var(--ui-border-strong);
    border-radius: var(--ui-radius-md);
}

textarea.form-control {
    min-height: 110px;
}

.form-control:focus,
.form-select:focus {
    border-color: #93c5fd;
    box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.12);
}

.form-control::placeholder {
    color: #94a3b8;
}

.form-text {
    color: var(--ui-text-muted);
}

.form-check-input:checked {
    background-color: var(--ui-primary);
    border-color: var(--ui-primary);
}
'@

Write-Utf8File ".\static\ui\css\tables.css" @'
.table-responsive {
    border: 1px solid var(--ui-border);
    border-radius: var(--ui-radius-lg);
    background: var(--ui-surface);
}

.table {
    margin-bottom: 0;
    color: var(--ui-text);
    vertical-align: middle;
}

.table > :not(caption) > * > * {
    padding: 0.85rem 1rem;
    border-bottom-color: var(--ui-border);
}

.table thead th {
    color: var(--ui-text-muted);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.035em;
    text-transform: uppercase;
    background: var(--ui-surface-muted);
    border-bottom-width: 1px;
}

.table tbody tr {
    transition: background-color var(--ui-transition-fast);
}

.table-hover > tbody > tr:hover > * {
    --bs-table-bg-state: #f8fbff;
}
'@

Write-Utf8File ".\static\ui\css\layout.css" @'
.app-shell {
    min-height: 100vh;
}

.app-content {
    min-height: calc(100vh - var(--ui-navbar-height));
}

.app-page {
    padding: 1.5rem;
}

.app-page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.app-page-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
}

.app-page-description {
    margin-top: 0.25rem;
    margin-bottom: 0;
    color: var(--ui-text-muted);
}

.app-page-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.625rem;
}
'@

Write-Utf8File ".\static\ui\css\responsive.css" @'
@media (max-width: 991.98px) {
    .app-page {
        padding: 1rem;
    }
}

@media (max-width: 767.98px) {
    .app-page-header {
        flex-direction: column;
    }

    .app-page-actions {
        width: 100%;
        justify-content: flex-start;
    }

    .app-page-actions .btn {
        flex: 1 1 auto;
    }
}
'@

Write-Utf8File ".\static\ui\js\app-shell.js" @'
(function () {
    "use strict";

    document.documentElement.classList.add("ui-js-enabled");
})();
'@

Write-Host ""
Write-Host "Executando validacoes..." -ForegroundColor Cyan

$checkOutput = python manage.py check 2>&1
$checkExitCode = $LASTEXITCODE

$testOutput = python manage.py test --keepdb 2>&1
$testExitCode = $LASTEXITCODE

$createdFiles = Get-ChildItem ".\static\ui" -Recurse -File |
    Sort-Object FullName |
    Select-Object FullName, Length

$reportPath = ".\diagnostico_ui_01a.txt"

$report = @"
=== DATA ===
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

=== ETAPA ===
UI-01A - Criacao segura de static/ui

=== BRANCH ===
$(git branch --show-current)

=== GIT STATUS ===
$(git status --short)

=== DJANGO CHECK ===
$($checkOutput | Out-String)

=== TESTES ===
$($testOutput | Out-String)

=== ARQUIVOS CRIADOS ===
$($createdFiles | Format-Table -AutoSize | Out-String)

=== DIFF RESUMIDO ===
$(git diff --stat)

=== BACKUP ===
$backupDir
"@

[System.IO.File]::WriteAllText(
    [System.IO.Path]::GetFullPath($reportPath),
    $report,
    $utf8SemBom
)

if ($checkExitCode -ne 0 -or $testExitCode -ne 0) {
    Write-Host ""
    Write-Host "A validacao encontrou erro. Nenhum template foi alterado." -ForegroundColor Red
    Write-Host "Relatorio: $reportPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " UI-01A CONCLUIDA SEM ALTERAR TEMPLATES" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Relatorio: $reportPath" -ForegroundColor Yellow
Write-Host "Backup: $backupDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "Nenhuma tela usa estes arquivos ainda." -ForegroundColor Cyan
Write-Host "Portanto, o comportamento visual atual permanece intacto." -ForegroundColor Cyan
