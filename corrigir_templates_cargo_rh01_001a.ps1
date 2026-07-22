param(
    [string]$ProjectRoot = "C:\Users\User\Alexandre\Projetos\cashback_system"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Sprint = "RH-01.001A"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogName = "aplicacao_rh01_001a_templates_cargo_$Timestamp.txt"
$BackupFolderName = ".backup_rh01_001a_templates_cargo_$Timestamp"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Diretorio do projeto nao encontrado: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

$LogPath = Join-Path $ProjectRoot $LogName
$BackupRoot = Join-Path $ProjectRoot $BackupFolderName
$SourceRoot = Join-Path $ProjectRoot "rh\templates\rh"
$TargetRoot = Join-Path $SourceRoot "cargo"

$TemplateNames = @(
    "list.html",
    "form.html",
    "delete.html"
)

Start-Transcript -LiteralPath $LogPath -Force | Out-Null

try {
    Write-Host "============================================================"
    Write-Host "$Sprint - Correcao dos templates de Cargo"
    Write-Host "============================================================"
    Write-Host "Projeto: $ProjectRoot"
    Write-Host "Origem: $SourceRoot"
    Write-Host "Destino: $TargetRoot"
    Write-Host "Backup: $BackupRoot"
    Write-Host "Log: $LogPath"

    Write-Host "`n[1/8] Validando branch..."

    $CurrentBranch = (git branch --show-current).Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao identificar a branch atual."
    }

    Write-Host "Branch atual: $CurrentBranch"

    if ($CurrentBranch -ne "feature/rh-01-fundacao") {
        throw "Branch incorreta. Esperado: feature/rh-01-fundacao"
    }

    Write-Host "`n[2/8] Validando estrutura atual..."

    if (-not (Test-Path -LiteralPath $SourceRoot)) {
        throw "Diretorio de templates do RH nao encontrado: $SourceRoot"
    }

    foreach ($TemplateName in $TemplateNames) {
        $SourcePath = Join-Path $SourceRoot $TemplateName
        $TargetPath = Join-Path $TargetRoot $TemplateName

        if ((Test-Path -LiteralPath $SourcePath) -and (Test-Path -LiteralPath $TargetPath)) {
            throw "Existem duas versoes do template $TemplateName. Revisao manual necessaria."
        }

        if (-not (Test-Path -LiteralPath $SourcePath) -and -not (Test-Path -LiteralPath $TargetPath)) {
            throw "Template nao encontrado nem na origem nem no destino: $TemplateName"
        }

        if (Test-Path -LiteralPath $TargetPath) {
            throw "O template ja esta no destino correto: $TargetPath"
        }

        Write-Host "OK - encontrado na origem: $SourcePath"
    }

    Write-Host "`n[3/8] Criando backup dos templates..."

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

    foreach ($TemplateName in $TemplateNames) {
        $SourcePath = Join-Path $SourceRoot $TemplateName
        $BackupPath = Join-Path $BackupRoot $TemplateName

        Copy-Item -LiteralPath $SourcePath -Destination $BackupPath -Force
        Write-Host "Backup criado: $BackupPath"
    }

    Write-Host "`n[4/8] Criando diretorio correto..."

    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
    Write-Host "Diretorio pronto: $TargetRoot"

    Write-Host "`n[5/8] Movendo templates de Cargo..."

    foreach ($TemplateName in $TemplateNames) {
        $SourcePath = Join-Path $SourceRoot $TemplateName
        $TargetPath = Join-Path $TargetRoot $TemplateName

        Move-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
        Write-Host "Movido: $SourcePath -> $TargetPath"
    }

    Write-Host "`n[6/8] Validando arquivos no destino..."

    foreach ($TemplateName in $TemplateNames) {
        $TargetPath = Join-Path $TargetRoot $TemplateName

        if (-not (Test-Path -LiteralPath $TargetPath)) {
            throw "Template nao encontrado no destino: $TargetPath"
        }

        $Length = (Get-Item -LiteralPath $TargetPath).Length

        if ($Length -le 0) {
            throw "Template vazio no destino: $TargetPath"
        }

        Write-Host "OK - $TargetPath ($Length bytes)"
    }

    Write-Host "`n[7/8] Validando carregamento pelo Django..."

    python manage.py shell -c "from django.template.loader import get_template; [get_template(n) for n in ('rh/cargo/list.html','rh/cargo/form.html','rh/cargo/delete.html')]; print('TEMPLATES_CARGO_OK')"

    if ($LASTEXITCODE -ne 0) {
        throw "O Django nao conseguiu carregar todos os templates de Cargo."
    }

    python manage.py check

    if ($LASTEXITCODE -ne 0) {
        throw "O django check falhou."
    }

    python manage.py test rh -v 2

    if ($LASTEXITCODE -ne 0) {
        throw "Os testes do modulo RH falharam."
    }

    Write-Host "`n[8/8] Exibindo diferencas e estado final..."

    git diff --check

    if ($LASTEXITCODE -ne 0) {
        throw "O git diff --check encontrou problemas."
    }

    git status --short
    Get-ChildItem -LiteralPath $TargetRoot -File |
        Select-Object Name, Length, LastWriteTime

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "$Sprint aplicado com sucesso." -ForegroundColor Green
    Write-Host "Templates corrigidos:"
    Write-Host "  rh/cargo/list.html"
    Write-Host "  rh/cargo/form.html"
    Write-Host "  rh/cargo/delete.html"
    Write-Host "Backup preservado em:"
    Write-Host $BackupRoot
    Write-Host "Log salvo em:"
    Write-Host $LogPath
    Write-Host "============================================================"
}
catch {
    Write-Host ""
    Write-Host "ERRO NA CORRECAO DOS TEMPLATES DE CARGO:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    if (Test-Path -LiteralPath $BackupRoot) {
        Write-Host "Restaurando estrutura anterior..." -ForegroundColor Yellow

        foreach ($TemplateName in $TemplateNames) {
            $BackupPath = Join-Path $BackupRoot $TemplateName
            $SourcePath = Join-Path $SourceRoot $TemplateName
            $TargetPath = Join-Path $TargetRoot $TemplateName

            if (Test-Path -LiteralPath $TargetPath) {
                Remove-Item -LiteralPath $TargetPath -Force
            }

            if (Test-Path -LiteralPath $BackupPath) {
                Copy-Item -LiteralPath $BackupPath -Destination $SourcePath -Force
            }
        }

        if ((Test-Path -LiteralPath $TargetRoot) -and
            -not (Get-ChildItem -LiteralPath $TargetRoot -Force | Select-Object -First 1)) {
            Remove-Item -LiteralPath $TargetRoot -Force
        }

        Write-Host "Estrutura anterior restaurada." -ForegroundColor Yellow
    }

    Write-Host "Consulte o log:"
    Write-Host $LogPath

    throw
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
    }
}
