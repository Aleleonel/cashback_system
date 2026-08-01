#requires -Version 5.1
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Write-Section {
    param([Parameter(Mandatory = $true)][string]$Title)
    Write-Host ""
    Write-Host ("=" * 78)
    Write-Host $Title
    Write-Host ("=" * 78)
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $true)][scriptblock]$Command,
        [switch]$AllowFailure
    )

    Write-Host ""
    Write-Host "Executando: $Description"

    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $Command
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previous
    }

    if (($exitCode -ne 0) -and (-not $AllowFailure)) {
        throw "Falha em: $Description (codigo $exitCode)"
    }

    return $exitCode
}

function Get-ProjectRoot {
    $root = (& git rev-parse --show-toplevel 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        throw "Execute este script dentro de um repositorio Git."
    }
    return $root
}

function Get-CurrentBranch {
    $branch = (& git branch --show-current 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
        throw "Nao foi possivel identificar a branch atual."
    }
    return $branch
}

function Get-RepoStatusEntries {
    $entries = @()
    $lines = & git status --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao consultar git status."
    }

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.Length -lt 4) {
            continue
        }

        $status = $line.Substring(0, 2)
        $path = $line.Substring(3).Trim()

        if ($path -match " -> ") {
            $path = ($path -split " -> ", 2)[1]
        }

        $entries += [PSCustomObject]@{
            Status = $status
            Path = $path.Replace("\", "/")
        }
    }

    return $entries
}

function Test-IsIgnoredPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $normalized = $Path.Replace("\", "/").TrimStart("./")

    $patterns = @(
        "diagnosticos/",
        "tools/diagnostics/",
        "__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        "htmlcov/",
        ".coverage",
        "coverage.xml",
        "*.pyc",
        "*.pyo",
        "*.log",
        "*.tmp"
    )

    foreach ($pattern in $patterns) {
        if ($pattern.EndsWith("/")) {
            if ($normalized.StartsWith($pattern, [System.StringComparison]::OrdinalIgnoreCase) -or
                $normalized.Contains("/$pattern")) {
                return $true
            }
        }
        elseif ($normalized -like $pattern) {
            return $true
        }
    }

    return $false
}

<#
Pipeline oficial do Cashback System
Etapa 01 - Diagnostico somente leitura
#>

param(
    [string]$TargetBranch = "develop",
    [string]$Remote = "origin"
)

try {
    $ProjectRoot = Get-ProjectRoot
    Set-Location $ProjectRoot

    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $DiagnosticsDir = Join-Path $ProjectRoot "diagnosticos"
    $ReportPath = Join-Path $DiagnosticsDir ("release_diagnostico_{0}.txt" -f $Timestamp)

    if (-not (Test-Path $DiagnosticsDir)) {
        New-Item -ItemType Directory -Path $DiagnosticsDir | Out-Null
    }

    Start-Transcript -Path $ReportPath -Force | Out-Null

    Write-Section "CASHBACK SYSTEM - DIAGNOSTICO DE RELEASE"
    Write-Host "Projeto: $ProjectRoot"
    Write-Host "Branch atual: $(Get-CurrentBranch)"
    Write-Host "Destino: $TargetBranch"
    Write-Host "Remoto: $Remote"
    Write-Host "Modo: SOMENTE LEITURA"

    Write-Section "1. FETCH"
    Invoke-Native -Description "git fetch --all --prune" -Command {
        git fetch --all --prune
    } | Out-Null

    Write-Section "2. STATUS"
    git status --short --branch

    Write-Section "3. ALTERACOES RELEVANTES"
    $entries = @(Get-RepoStatusEntries)
    $relevant = @($entries | Where-Object { -not (Test-IsIgnoredPath $_.Path) })
    $ignored = @($entries | Where-Object { Test-IsIgnoredPath $_.Path })

    if ($relevant.Count -eq 0) {
        Write-Host "Nenhuma alteracao relevante encontrada."
    }
    else {
        $relevant | Format-Table -AutoSize | Out-String | Write-Host
    }

    Write-Section "4. ARTEFATOS IGNORADOS"
    if ($ignored.Count -eq 0) {
        Write-Host "Nenhum artefato temporario encontrado."
    }
    else {
        $ignored | Format-Table -AutoSize | Out-String | Write-Host
    }

    Write-Section "5. DIFF CHECK"
    Invoke-Native -Description "git diff --check" -Command {
        git diff --check
    } | Out-Null

    Write-Section "6. RELACAO COM DESTINO"
    $current = Get-CurrentBranch
    $targetRef = "$Remote/$TargetBranch"

    & git show-ref --verify --quiet "refs/remotes/$Remote/$TargetBranch"
    if ($LASTEXITCODE -ne 0) {
        $targetRef = $TargetBranch
    }

    Write-Host "Referencia de comparacao: $targetRef"
    git rev-list --left-right --count "$targetRef...$current"
    git log --oneline --decorate "$targetRef..$current"

    Write-Section "7. BRANCHES NAO MERGEADAS"
    git branch -a --no-merged $targetRef

    Write-Section "DIAGNOSTICO CONCLUIDO"
    Write-Host "Relatorio: $ReportPath"
}
catch {
    Write-Host ""
    Write-Host "DIAGNOSTICO INTERROMPIDO:"
    Write-Host $_.Exception.Message
    exit 1
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
}
