param(
    [string]$ProjectRoot = "C:\Users\User\Alexandre\Projetos\cashback_system"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Sprint = "RH-01.002A"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogName = "aplicacao_rh01_002a_sidebar_$Timestamp.txt"
$BackupFolderName = ".backup_rh01_002a_sidebar_$Timestamp"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $Encoding)
}

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Diretorio do projeto nao encontrado: $ProjectRoot"
}

Set-Location -LiteralPath $ProjectRoot

$SidebarRelative = "templates\partials\sidebar.html"
$SidebarPath = Join-Path $ProjectRoot $SidebarRelative
$LogPath = Join-Path $ProjectRoot $LogName
$BackupRoot = Join-Path $ProjectRoot $BackupFolderName
$BackupPath = Join-Path $BackupRoot $SidebarRelative

if (-not (Test-Path -LiteralPath $SidebarPath)) {
    throw "Sidebar nao encontrada: $SidebarPath"
}

Start-Transcript -LiteralPath $LogPath -Force | Out-Null

try {
    Write-Host "============================================================"
    Write-Host "$Sprint - Integracao do RH na sidebar"
    Write-Host "============================================================"
    Write-Host "Projeto: $ProjectRoot"
    Write-Host "Sidebar: $SidebarPath"
    Write-Host "Log: $LogPath"
    Write-Host "Backup: $BackupRoot"

    Write-Host "`n[1/8] Validando branch e estado do repositorio..."

    $CurrentBranch = (git branch --show-current).Trim()

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao identificar a branch atual."
    }

    Write-Host "Branch atual: $CurrentBranch"

    if ($CurrentBranch -ne "feature/rh-01-fundacao") {
        throw "Branch incorreta. Esperado: feature/rh-01-fundacao"
    }

    $StatusBefore = @(git status --short)

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao consultar o estado do Git."
    }

    $AllowedPatterns = @(
        "aplicar_rh01_002_departamento\.ps1$",
        "diagnostico_rh01_002_departamento\.ps1$",
        "diagnostico_sidebar_rh01_002\.txt$",
        "corrigir_sidebar_rh01_002a.*\.ps1$",
        "aplicacao_rh01_002_departamento_.*\.txt$",
        "aplicacao_rh01_002a_sidebar_.*\.txt$",
        "\.backup_rh01_002_departamento_.*",
        "\.backup_rh01_002a_sidebar_.*",
        "rh/(admin\.py|models/__init__\.py|urls\.py)$",
        "rh/(forms|migrations|models|selectors|services|templates|tests|views)/",
        "templates/partials/sidebar\.html$"
    )

    $UnexpectedChanges = @()

    foreach ($Line in $StatusBefore) {
        if (-not $Line) {
            continue
        }

        $Allowed = $false

        foreach ($Pattern in $AllowedPatterns) {
            if ($Line -match $Pattern) {
                $Allowed = $true
                break
            }
        }

        if (-not $Allowed) {
            $UnexpectedChanges += $Line
        }
    }

    if ($UnexpectedChanges.Count -gt 0) {
        Write-Host "Alteracoes inesperadas encontradas:" -ForegroundColor Yellow
        $UnexpectedChanges | ForEach-Object { Write-Host $_ }
        throw "Existem alteracoes fora do escopo esperado."
    }

    Write-Host "`n[2/8] Validando URLs do RH..."

    python manage.py shell -c "from django.urls import reverse; print(reverse('rh:cargo_list')); print(reverse('rh:departamento_list'))"

    if ($LASTEXITCODE -ne 0) {
        throw "As URLs de Cargo ou Departamento nao puderam ser resolvidas."
    }

    Write-Host "`n[3/8] Criando backup da sidebar..."

    $BackupDirectory = Split-Path -Parent $BackupPath
    New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
    Copy-Item -LiteralPath $SidebarPath -Destination $BackupPath -Force

    Write-Host "Backup criado: $BackupPath"

    Write-Host "`n[4/8] Analisando conteudo atual..."

    $SidebarContent = [System.IO.File]::ReadAllText($SidebarPath)

    $StartMarker = "<!-- UI-RH-INICIO -->"
    $EndMarker = "<!-- UI-RH-FIM -->"

    if ($SidebarContent.Contains($StartMarker) -or $SidebarContent.Contains($EndMarker)) {
        throw "A secao RH ja possui marcadores. Nenhuma duplicacao sera criada."
    }

    if ($SidebarContent -match "rh:cargo_list" -or $SidebarContent -match "rh:departamento_list") {
        throw "A sidebar ja contem pelo menos um link do RH. Revise manualmente antes de aplicar."
    }

    $Anchor = @'
        {% if pode_ver_campanhas or pode_configurar_campanhas or pode_templates_campanhas %}
'@

    if (-not $SidebarContent.Contains($Anchor)) {
        throw "Ponto de insercao nao encontrado antes da secao Campanhas."
    }

    Write-Host "`n[5/8] Inserindo secao Recursos Humanos..."

    $RhBlock = @'
        <!-- UI-RH-INICIO -->
        <div class="mt-4 mb-1 px-3">
            <div
                class="text-uppercase text-white-50 small fw-semibold"
                style="letter-spacing: .06em;"
            >
                Recursos Humanos
            </div>
        </div>

        <a
            href="{% url 'rh:cargo_list' %}"
            class="nav-link {% if request.resolver_match.namespace == 'rh' and request.resolver_match.url_name == 'cargo_list' %}active bg-primary text-white{% else %}text-white{% endif %}"
            data-menu-rh-cargos="true"
        >
            <i class="bi bi-briefcase me-2"></i>
            Cargos
        </a>

        <a
            href="{% url 'rh:departamento_list' %}"
            class="nav-link {% if request.resolver_match.namespace == 'rh' and request.resolver_match.url_name == 'departamento_list' %}active bg-primary text-white{% else %}text-white{% endif %}"
            data-menu-rh-departamentos="true"
        >
            <i class="bi bi-diagram-3 me-2"></i>
            Departamentos
        </a>
        <!-- UI-RH-FIM -->

'@

    $UpdatedContent = $SidebarContent.Replace(
        $Anchor,
        $RhBlock + $Anchor
    )

    if ($UpdatedContent -eq $SidebarContent) {
        throw "Nenhuma alteracao foi aplicada a sidebar."
    }

    Write-Utf8NoBom -Path $SidebarPath -Content $UpdatedContent

    Write-Host "`n[6/8] Validando alteracao aplicada..."

    $SavedContent = [System.IO.File]::ReadAllText($SidebarPath)

    $RequiredSnippets = @(
        "<!-- UI-RH-INICIO -->",
        "<!-- UI-RH-FIM -->",
        "{% url 'rh:cargo_list' %}",
        "{% url 'rh:departamento_list' %}",
        "data-menu-rh-cargos=""true""",
        "data-menu-rh-departamentos=""true"""
    )

    foreach ($Snippet in $RequiredSnippets) {
        if (-not $SavedContent.Contains($Snippet)) {
            throw "Trecho obrigatorio nao encontrado depois da gravacao: $Snippet"
        }

        Write-Host "OK - $Snippet"
    }

    $CargoOccurrences = (
        [regex]::Matches(
            $SavedContent,
            [regex]::Escape("{% url 'rh:cargo_list' %}")
        )
    ).Count

    $DepartamentoOccurrences = (
        [regex]::Matches(
            $SavedContent,
            [regex]::Escape("{% url 'rh:departamento_list' %}")
        )
    ).Count

    if ($CargoOccurrences -ne 1) {
        throw "Quantidade inesperada de links de Cargo: $CargoOccurrences"
    }

    if ($DepartamentoOccurrences -ne 1) {
        throw "Quantidade inesperada de links de Departamento: $DepartamentoOccurrences"
    }

    Write-Host "`n[7/8] Executando validacoes Django..."

    python manage.py check

    if ($LASTEXITCODE -ne 0) {
        throw "O django check falhou."
    }

    python manage.py test rh -v 2

    if ($LASTEXITCODE -ne 0) {
        throw "Os testes do modulo RH falharam."
    }

    Write-Host "`n[8/8] Exibindo estado final..."

    git diff --check

    if ($LASTEXITCODE -ne 0) {
        throw "O git diff --check encontrou problemas de formatacao."
    }

    git diff -- $SidebarRelative
    git status --short

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "$Sprint aplicado com sucesso." -ForegroundColor Green
    Write-Host "A sidebar agora possui a secao Recursos Humanos."
    Write-Host "Links adicionados: Cargos e Departamentos."
    Write-Host "Backup preservado em:"
    Write-Host $BackupRoot
    Write-Host "Log salvo em:"
    Write-Host $LogPath
    Write-Host "============================================================"
}
catch {
    Write-Host ""
    Write-Host "ERRO NA CORRECAO DA SIDEBAR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    if (Test-Path -LiteralPath $BackupPath) {
        Copy-Item -LiteralPath $BackupPath -Destination $SidebarPath -Force
        Write-Host "Sidebar restaurada a partir do backup." -ForegroundColor Yellow
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
        # Ignora falha caso o transcript nao tenha sido iniciado.
    }
}
