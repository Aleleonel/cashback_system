Set-StrictMode -Version Latest

$automacaoModule = Join-Path $PSScriptRoot "Projeto.Automacao.psm1"
Import-Module $automacaoModule -Force -ErrorAction Stop

function Get-ProjetoGitBranch {
    [CmdletBinding()]
    param()

    $branch = @(& git branch --show-current 2>$null)
    $codigo = $LASTEXITCODE

    if ($codigo -ne 0) {
        throw "Nao foi possivel identificar a branch atual."
    }

    return (($branch | Out-String).Trim())
}

function Get-ProjetoGitStatus {
    [CmdletBinding()]
    param()

    return @(& git status --short 2>&1)
}

function Test-ProjetoGitDiff {
    [CmdletBinding()]
    param(
        [string]$Relatorio
    )

    return Invoke-ProjetoCommand `
        -Titulo "VALIDACAO DO DIFF GIT" `
        -Relatorio $Relatorio `
        -Comando {
            git diff --check
        }
}

function Add-ProjetoArquivos {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arquivos,

        [string]$Relatorio
    )

    foreach ($arquivo in $Arquivos) {
        if (-not (Test-Path -LiteralPath $arquivo)) {
            throw "Arquivo nao encontrado para staging: $arquivo"
        }
    }

    return Invoke-ProjetoCommand `
        -Titulo "STAGING SELETIVO" `
        -Relatorio $Relatorio `
        -Comando {
            foreach ($arquivo in $Arquivos) {
                git add -- $arquivo
            }
        }
}

function Commit-Projeto {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Mensagem,

        [string]$Relatorio
    )

    return Invoke-ProjetoCommand `
        -Titulo "CRIACAO DO COMMIT" `
        -Relatorio $Relatorio `
        -Comando {
            git commit -m $Mensagem
        }
}

function Push-Projeto {
    [CmdletBinding()]
    param(
        [string]$Remote = "origin",
        [string]$Branch = (Get-ProjetoGitBranch),
        [string]$Relatorio
    )

    return Invoke-ProjetoCommand `
        -Titulo "PUSH PARA O REPOSITORIO REMOTO" `
        -Relatorio $Relatorio `
        -Comando {
            git push $Remote $Branch
        }
}

Export-ModuleMember -Function `
    Get-ProjetoGitBranch, `
    Get-ProjetoGitStatus, `
    Test-ProjetoGitDiff, `
    Add-ProjetoArquivos, `
    Commit-Projeto, `
    Push-Projeto
