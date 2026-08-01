Set-StrictMode -Version Latest

$automacaoModule = Join-Path $PSScriptRoot "Projeto.Automacao.psm1"
Import-Module $automacaoModule -Force -ErrorAction Stop

function Invoke-DjangoCheck {
    [CmdletBinding()]
    param(
        [string]$Relatorio
    )

    return Invoke-ProjetoCommand `
        -Titulo "DJANGO CHECK" `
        -Relatorio $Relatorio `
        -Comando {
            python .\manage.py check
        }
}

function Invoke-TestesDjango {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Alvos,

        [int]$Verbosity = 1,

        [string]$Relatorio,

        [switch]$PermitirFalha
    )

    $titulo = "TESTES DJANGO - " + ($Alvos -join ", ")

    return Invoke-ProjetoCommand `
        -Titulo $titulo `
        -Relatorio $Relatorio `
        -PermitirFalha:$PermitirFalha `
        -Comando {
            python .\manage.py test @Alvos -v $Verbosity
        }
}

function Invoke-TestesModulo {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Modulo,

        [int]$Verbosity = 1,

        [string]$Relatorio,

        [switch]$PermitirFalha
    )

    return Invoke-TestesDjango `
        -Alvos @($Modulo) `
        -Verbosity $Verbosity `
        -Relatorio $Relatorio `
        -PermitirFalha:$PermitirFalha
}

Export-ModuleMember -Function `
    Invoke-DjangoCheck, `
    Invoke-TestesDjango, `
    Invoke-TestesModulo
