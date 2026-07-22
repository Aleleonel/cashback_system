param(
    [string]$ProjectRoot = "C:\Users\User\Alexandre\Projetos\cashback_system"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================"
Write-Host "RH-01.002 - Diagnostico para Departamento"
Write-Host "============================================================"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Diretorio do projeto nao encontrado: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

$RequiredFiles = @(
    "manage.py",
    "rh\models\cargo.py",
    "rh\models\__init__.py",
    "rh\forms\cargo_form.py",
    "rh\selectors\cargo_selector.py",
    "rh\services\cargo_service.py",
    "rh\views\cargo_views.py",
    "rh\urls.py",
    "rh\admin.py",
    "rh\tests\test_urls.py",
    "rh\migrations\0001_initial.py"
)

Write-Host "`n[1/10] Conferindo arquivos obrigatorios..."

foreach ($RelativePath in $RequiredFiles) {
    $FullPath = Join-Path $ProjectRoot $RelativePath

    if (-not (Test-Path -LiteralPath $FullPath)) {
        throw "Arquivo obrigatorio nao encontrado: $RelativePath"
    }

    Write-Host "OK - $RelativePath"
}

Write-Host "`n[2/10] Estado atual do Git..."
git status --short
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao consultar o Git."
}

Write-Host "`nBranch atual:"
git branch --show-current

Write-Host "`nUltimos commits:"
git log --oneline --decorate -5

Write-Host "`n[3/10] Estrutura atual do modulo RH..."
Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "rh") -Recurse |
    Where-Object {
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Select-Object FullName

Write-Host "`n[4/10] Arquivos de referencia do Cargo..."

$ReferenceFiles = @(
    "rh\models\cargo.py",
    "rh\models\__init__.py",
    "rh\forms\cargo_form.py",
    "rh\selectors\cargo_selector.py",
    "rh\services\cargo_service.py",
    "rh\views\cargo_views.py",
    "rh\urls.py",
    "rh\admin.py",
    "rh\tests\test_urls.py"
)

foreach ($RelativePath in $ReferenceFiles) {
    $FullPath = Join-Path $ProjectRoot $RelativePath
    Write-Host "`n---------------- BEGIN $RelativePath ----------------"
    Get-Content -LiteralPath $FullPath -Encoding UTF8
    Write-Host "----------------- END $RelativePath -----------------"
}

Write-Host "`n[5/10] Templates atuais do RH..."

$TemplateFiles = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "rh\templates\rh") -Recurse -File |
    Where-Object {
        $_.Extension -in @(".html", ".txt")
    }

if ($TemplateFiles) {
    foreach ($TemplateFile in $TemplateFiles) {
        $Relative = $TemplateFile.FullName.Substring($ProjectRoot.Length + 1)
        Write-Host "`n---------------- BEGIN $Relative ----------------"
        Get-Content -LiteralPath $TemplateFile.FullName -Encoding UTF8
        Write-Host "----------------- END $Relative -----------------"
    }
}
else {
    Write-Warning "Nenhum template encontrado em rh\templates\rh."
}

Write-Host "`n[6/10] Verificando como a matriz do usuario e obtida..."

$MatrizPatterns = @(
    'request\.user',
    'matriz',
    'get_matriz',
    'matriz_id',
    'usuario\.matriz'
)

foreach ($Pattern in $MatrizPatterns) {
    Write-Host "`nPadrao: $Pattern"

    $Matches = Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.py" |
        Where-Object {
            $_.FullName -notmatch '\\venv\\' -and
            $_.FullName -notmatch '\\__pycache__\\' -and
            $_.FullName -notmatch '\\migrations\\'
        } |
        Select-String -Pattern $Pattern

    if ($Matches) {
        $Matches |
            Select-Object -First 80 |
            ForEach-Object {
                Write-Host ("{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim())
            }
    }
    else {
        Write-Host "Nenhuma referencia encontrada."
    }
}

Write-Host "`n[7/10] Procurando entidade Departamento existente..."

$DepartamentoMatches = Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.py" |
    Where-Object {
        $_.FullName -notmatch '\\venv\\' -and
        $_.FullName -notmatch '\\__pycache__\\'
    } |
    Select-String -Pattern 'Departamento|departamento'

if ($DepartamentoMatches) {
    $DepartamentoMatches | ForEach-Object {
        Write-Host ("{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim())
    }
}
else {
    Write-Host "Nenhuma entidade ou referencia Departamento encontrada."
}

Write-Host "`n[8/10] Validacoes atuais do Django..."

python manage.py check
if ($LASTEXITCODE -ne 0) {
    throw "O projeto possui erro no django check antes da implementacao."
}

python manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) {
    throw "Existem alteracoes de model sem migration antes da implementacao."
}

python manage.py showmigrations rh
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao consultar migrations do RH."
}

python manage.py test rh -v 2
if ($LASTEXITCODE -ne 0) {
    throw "Os testes atuais do RH nao estao passando."
}

Write-Host "`n[9/10] Verificando sintaxe dos arquivos principais..."

python -m py_compile `
    (Join-Path $ProjectRoot "rh\models\cargo.py") `
    (Join-Path $ProjectRoot "rh\models\__init__.py") `
    (Join-Path $ProjectRoot "rh\forms\cargo_form.py") `
    (Join-Path $ProjectRoot "rh\selectors\cargo_selector.py") `
    (Join-Path $ProjectRoot "rh\services\cargo_service.py") `
    (Join-Path $ProjectRoot "rh\views\cargo_views.py") `
    (Join-Path $ProjectRoot "rh\urls.py") `
    (Join-Path $ProjectRoot "rh\admin.py")

if ($LASTEXITCODE -ne 0) {
    throw "Falha na validacao de sintaxe."
}

Write-Host "`n[10/10] Resumo..."
Write-Host "O diagnostico reuniu o padrao atual do Cargo para replicacao segura."
Write-Host "Nenhum arquivo do projeto foi alterado."

Write-Host "`n============================================================"
Write-Host "Diagnostico RH-01.002 concluido."
Write-Host "Nenhum arquivo foi alterado."
Write-Host "============================================================"
