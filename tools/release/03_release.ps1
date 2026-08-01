#requires -Version 5.1

param(
    [Parameter(Mandatory = $true)][string]$FeatureBranch,
    [string]$TargetBranch = "develop",
    [string]$Remote = "origin",
    [Parameter(Mandatory = $true)][string]$CommitMessage,
    [Parameter(Mandatory = $true)][string]$MergeMessage,
    [string[]]$TestApps = @(),
    [switch]$FullTestSuite
)

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
Etapa 03 - Release e merge

Exemplo RH:
.\03_release.ps1 `
  -FeatureBranch "feature/rh-02-cadastro-cargos" `
  -TargetBranch "develop" `
  -CommitMessage "feat(ui): conclui padronizacao visual de pedidos de compra" `
  -MergeMessage "merge: incorpora modulo RH na develop" `
  -TestApps rh,compras
#>



function Invoke-Validations {
    param([string]$Stage)

    Write-Section "VALIDACOES - $Stage"

    Invoke-Native -Description "git diff --check" -Command {
        git diff --check
    } | Out-Null

    Invoke-Native -Description "python manage.py check" -Command {
        python manage.py check
    } | Out-Null

    Invoke-Native -Description "python manage.py makemigrations --check --dry-run" -Command {
        python manage.py makemigrations --check --dry-run
    } | Out-Null

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
        Invoke-Native -Description "python manage.py test" -Command {
            python manage.py test
        } | Out-Null
    }
}

try {
    $ProjectRoot = Get-ProjectRoot
    Set-Location $ProjectRoot

    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $DiagnosticsDir = Join-Path $ProjectRoot "diagnosticos"
    $ReportPath = Join-Path $DiagnosticsDir ("release_aplicacao_{0}.txt" -f $Timestamp)
    $PatchPath = Join-Path $DiagnosticsDir ("release_backup_{0}.patch" -f $Timestamp)
    $SafetyTag = "safety/pre-merge-$($FeatureBranch.Replace('/', '-'))-$Timestamp"

    if (-not (Test-Path $DiagnosticsDir)) {
        New-Item -ItemType Directory -Path $DiagnosticsDir | Out-Null
    }

    Start-Transcript -Path $ReportPath -Force | Out-Null

    Write-Section "CASHBACK SYSTEM - RELEASE"
    Write-Host "Feature: $FeatureBranch"
    Write-Host "Destino: $TargetBranch"
    Write-Host "Tag de seguranca: $SafetyTag"

    $current = Get-CurrentBranch
    if ($current -ne $FeatureBranch) {
        throw "Branch atual '$current'. Esperada '$FeatureBranch'."
    }

    Write-Section "1. FETCH"
    Invoke-Native -Description "git fetch $Remote --prune" -Command {
        git fetch $Remote --prune
    } | Out-Null

    Write-Section "2. VALIDAR ALTERACOES"
    $entries = @(Get-RepoStatusEntries)
    $relevant = @($entries | Where-Object { -not (Test-IsIgnoredPath $_.Path) })

    if ($relevant.Count -eq 0) {
        Write-Host "Nenhuma alteracao relevante para commit."
    }
    else {
        $relevant | Format-Table -AutoSize | Out-String | Write-Host
    }

    Write-Section "3. BACKUP"
    Invoke-Native -Description "criar patch de backup" -Command {
        git -c core.safecrlf=false diff --binary --output="$PatchPath"
    } | Out-Null

    Write-Host "Patch: $PatchPath"

    Invoke-Validations -Stage "ANTES DO COMMIT"

    Write-Section "4. COMMIT DA FEATURE"
    if ($relevant.Count -gt 0) {
        foreach ($entry in $relevant) {
            git add -- $entry.Path
            if ($LASTEXITCODE -ne 0) {
                throw "Falha ao adicionar: $($entry.Path)"
            }
        }

        Invoke-Native -Description "git commit" -Command {
            git commit -m $CommitMessage
        } | Out-Null
    }
    else {
        Write-Host "Feature sem alteracoes locais; usando commits ja existentes."
    }

    Write-Section "5. PUSH DA FEATURE"
    Invoke-Native -Description "git push da feature" -Command {
        git push -u $Remote $FeatureBranch
    } | Out-Null

    $remainingRelevant = @(
        Get-RepoStatusEntries | Where-Object { -not (Test-IsIgnoredPath $_.Path) }
    )

    if ($remainingRelevant.Count -gt 0) {
        throw "A arvore de trabalho possui alteracoes relevantes apos o commit."
    }

    Write-Section "6. PREPARAR DESTINO"
    Invoke-Native -Description "git checkout $TargetBranch" -Command {
        git checkout $TargetBranch
    } | Out-Null

    Invoke-Native -Description "git pull --ff-only" -Command {
        git pull --ff-only $Remote $TargetBranch
    } | Out-Null

    Invoke-Native -Description "criar tag local de seguranca" -Command {
        git tag $SafetyTag
    } | Out-Null

    Write-Section "7. MERGE"
    Invoke-Native -Description "merge --no-ff" -Command {
        git merge --no-ff $FeatureBranch -m $MergeMessage
    } | Out-Null

    Invoke-Validations -Stage "DEPOIS DO MERGE"

    Write-Section "8. PUSH DO DESTINO"
    Invoke-Native -Description "git push $Remote $TargetBranch" -Command {
        git push $Remote $TargetBranch
    } | Out-Null

    Write-Section "9. RESULTADO"
    git status --short --branch
    git log --oneline --decorate -8

    Write-Host ""
    Write-Host "Release concluida."
    Write-Host "Tag local de seguranca: $SafetyTag"
    Write-Host "Patch: $PatchPath"
    Write-Host "Relatorio: $ReportPath"
}
catch {
    Write-Host ""
    Write-Host ("!" * 78)
    Write-Host "RELEASE INTERROMPIDA"
    Write-Host ("!" * 78)
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Use 04_rollback.ps1 somente apos revisar o relatorio."
    exit 1
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
}
