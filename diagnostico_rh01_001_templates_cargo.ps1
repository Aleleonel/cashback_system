param(
    [string]$ProjectRoot = "C:\Users\User\Alexandre\Projetos\cashback_system"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogName = "diagnostico_rh01_001_templates_cargo_$Timestamp.txt"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Diretorio do projeto nao encontrado: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot
$LogPath = Join-Path $ProjectRoot $LogName

Start-Transcript -LiteralPath $LogPath -Force | Out-Null

try {
    Write-Host "============================================================"
    Write-Host "RH-01.001 - Diagnostico dos templates de Cargo"
    Write-Host "============================================================"

    Write-Host "`n[1/6] View de Cargo"
    if (Test-Path ".\rh\views\cargo_views.py") {
        Get-Content ".\rh\views\cargo_views.py"
    }
    else {
        Write-Host "Arquivo nao encontrado: rh\views\cargo_views.py"
    }

    Write-Host "`n[2/6] Templates existentes no modulo RH"
    if (Test-Path ".\rh\templates") {
        Get-ChildItem ".\rh\templates" -Recurse -File |
            Select-Object FullName, Length, LastWriteTime
    }
    else {
        Write-Host "Diretorio nao encontrado: rh\templates"
    }

    Write-Host "`n[3/6] Referencias a templates de Cargo"
    Get-ChildItem ".\rh" -Recurse -File -Include *.py,*.html |
        Select-String -Pattern "rh/cargo|cargo/list|cargo_form|cargo_confirm|render\(" |
        Select-Object Path, LineNumber, Line

    Write-Host "`n[4/6] URLs de Cargo"
    if (Test-Path ".\rh\urls.py") {
        Get-Content ".\rh\urls.py"
    }

    Write-Host "`n[5/6] Teste de resolucao de template"
    python manage.py shell -c "from django.template.loader import get_template; get_template('rh/cargo/list.html'); print('TEMPLATE_OK')"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Template rh/cargo/list.html nao foi localizado." -ForegroundColor Yellow
    }

    Write-Host "`n[6/6] Estado do Git"
    git status --short

    Write-Host ""
    Write-Host "Diagnostico concluido."
    Write-Host "Nenhum arquivo foi alterado."
    Write-Host "Log salvo em:"
    Write-Host $LogPath
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
}
