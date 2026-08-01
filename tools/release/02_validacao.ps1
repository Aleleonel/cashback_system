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
Etapa 02 - Validacao tecnica
#>

param(
    [string[]]$TestApps = @(),
    [switch]$FullTestSuite
)

try {
    $ProjectRoot = Get-ProjectRoot
    Set-Location $ProjectRoot

    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $DiagnosticsDir = Join-Path $ProjectRoot "diagnosticos"
    $ReportPath = Join-Path $DiagnosticsDir ("release_validacao_{0}.txt" -f $Timestamp)

    if (-not (Test-Path $DiagnosticsDir)) {
        New-Item -ItemType Directory -Path $DiagnosticsDir | Out-Null
    }

    Start-Transcript -Path $ReportPath -Force | Out-Null

    Write-Section "CASHBACK SYSTEM - VALIDACAO DE RELEASE"
    Write-Host "Projeto: $ProjectRoot"
    Write-Host "Branch: $(Get-CurrentBranch)"

    Write-Section "1. GIT DIFF CHECK"
    Invoke-Native -Description "git diff --check" -Command {
        git diff --check
    } | Out-Null

    Write-Section "2. DJANGO CHECK"
    Invoke-Native -Description "python manage.py check" -Command {
        python manage.py check
    } | Out-Null

    Write-Section "3. MIGRACOES"
    Invoke-Native -Description "python manage.py makemigrations --check --dry-run" -Command {
        python manage.py makemigrations --check --dry-run
    } | Out-Null

    Write-Section "4. TESTES"
    if ($FullTestSuite) {
        Invoke-Native -Description "python manage.py test" -Command {
            python manage.py test
        } | Out-Null
    }
    elseif ($TestApps.Count -gt 0) {
        foreach ($app in $TestApps) {
            $appName = $app
            Invoke-Native -Description "python manage.py test $appName" -Command {
                python manage.py test $appName
            } | Out-Null
        }
    }
    else {
        Write-Host "Nenhum app informado. Executando suite completa."
        Invoke-Native -Description "python manage.py test" -Command {
            python manage.py test
        } | Out-Null
    }

    Write-Section "VALIDACAO APROVADA"
    Write-Host "Relatorio: $ReportPath"
}
catch {
    Write-Host ""
    Write-Host "VALIDACAO REPROVADA:"
    Write-Host $_.Exception.Message
    exit 1
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
}
