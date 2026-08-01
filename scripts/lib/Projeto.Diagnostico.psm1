Set-StrictMode -Version Latest

$automacaoModule = Join-Path $PSScriptRoot "Projeto.Automacao.psm1"
Import-Module $automacaoModule -Force -ErrorAction Stop

function Find-ProjetoOcorrencias {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Raizes,

        [Parameter(Mandatory)]
        [string[]]$Padroes,

        [string[]]$Extensoes = @(".py", ".html", ".js", ".ps1", ".psm1"),

        [string]$Relatorio
    )

    foreach ($padrao in $Padroes) {
        Write-ProjetoSecao -Titulo ("BUSCA: " + $padrao) -Relatorio $Relatorio

        foreach ($raiz in $Raizes) {
            if (-not (Test-Path -LiteralPath $raiz)) {
                continue
            }

            Get-ChildItem -LiteralPath $raiz -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object {
                    ($_.Extension -in $Extensoes) -and
                    ($_.FullName -notmatch "\\__pycache__\\")
                } |
                Select-String -SimpleMatch -Pattern $padrao |
                ForEach-Object {
                    $linha = "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
                    Write-ProjetoLog -Mensagem $linha -Relatorio $Relatorio -SemPrefixo
                }
        }
    }
}

function Get-ProjetoArquivos {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Raizes,

        [string[]]$Extensoes = @(".py", ".html", ".js"),

        [string]$Relatorio
    )

    foreach ($raiz in $Raizes) {
        if (-not (Test-Path -LiteralPath $raiz)) {
            continue
        }

        Get-ChildItem -LiteralPath $raiz -Recurse -File |
            Where-Object {
                ($_.Extension -in $Extensoes) -and
                ($_.FullName -notmatch "\\__pycache__\\")
            } |
            Sort-Object FullName |
            ForEach-Object {
                Write-ProjetoLog -Mensagem $_.FullName -Relatorio $Relatorio -SemPrefixo
            }
    }
}

Export-ModuleMember -Function `
    Find-ProjetoOcorrencias, `
    Get-ProjetoArquivos
