$ErrorActionPreference = "Continue"

$PastaDocumentacao = Join-Path (Get-Location) "tem_chatgpt"
$ArquivoEvidencias = Join-Path $PastaDocumentacao "07_EVIDENCIAS_TESTES.txt"
$DataAtual = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$BranchAtual = git branch --show-current 2>&1 | Out-String
$StatusGit = git status --short 2>&1 | Out-String
$DjangoCheck = python manage.py check 2>&1 | Out-String
$MigrationCheck = python manage.py makemigrations --check --dry-run 2>&1 | Out-String
$TestesEstoque = python manage.py test estoque 2>&1 | Out-String

@"
CASHBACK SYSTEM
EVIDÊNCIAS DE VERIFICAÇÃO

Gerado em: $DataAtual

================================================
BRANCH
================================================

$BranchAtual

================================================
GIT STATUS
================================================

$StatusGit

================================================
DJANGO CHECK
================================================

$DjangoCheck

================================================
MAKEMIGRATIONS --CHECK --DRY-RUN
================================================

$MigrationCheck

================================================
TESTES DO MÓDULO DE ESTOQUE
================================================

$TestesEstoque
"@ | Set-Content -Path $ArquivoEvidencias -Encoding UTF8

Write-Host ""
Write-Host "Evidências atualizadas em:"
Write-Host $ArquivoEvidencias
