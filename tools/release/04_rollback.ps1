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
Etapa 04 - Rollback local controlado

Este script NAO executa push --force.
Ele restaura a branch local de destino para uma tag de seguranca.
#>

param(
    [Parameter(Mandatory = $true)][string]$SafetyTag,
    [string]$TargetBranch = "develop",
    [string]$Remote = "origin"
)

try {
    $ProjectRoot = Get-ProjectRoot
    Set-Location $ProjectRoot

    Write-Section "CASHBACK SYSTEM - ROLLBACK LOCAL"
    Write-Host "Destino: $TargetBranch"
    Write-Host "Tag: $SafetyTag"

    $entries = @(Get-RepoStatusEntries)
    $relevant = @($entries | Where-Object { -not (Test-IsIgnoredPath $_.Path) })

    if ($relevant.Count -gt 0) {
        throw "Existem alteracoes locais relevantes. O rollback foi bloqueado."
    }

    & git show-ref --tags --verify --quiet "refs/tags/$SafetyTag"
    if ($LASTEXITCODE -ne 0) {
        throw "Tag de seguranca nao encontrada: $SafetyTag"
    }

    Invoke-Native -Description "checkout $TargetBranch" -Command {
        git checkout $TargetBranch
    } | Out-Null

    $backupBranch = "backup/$TargetBranch-pre-rollback-$(Get-Date -Format 'yyyyMMdd_HHmmss')"

    Invoke-Native -Description "criar branch de backup" -Command {
        git branch $backupBranch
    } | Out-Null

    Invoke-Native -Description "reset --hard para tag de seguranca" -Command {
        git reset --hard $SafetyTag
    } | Out-Null

    Write-Section "ROLLBACK LOCAL CONCLUIDO"
    Write-Host "Branch de backup: $backupBranch"
    Write-Host "Branch restaurada localmente: $TargetBranch"
    Write-Host ""
    Write-Host "Nenhum push foi executado."
    Write-Host "Revise e valide antes de qualquer operacao remota."
}
catch {
    Write-Host ""
    Write-Host "ROLLBACK INTERROMPIDO:"
    Write-Host $_.Exception.Message
    exit 1
}
