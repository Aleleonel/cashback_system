Set-StrictMode -Version Latest

$relatorioModule = Join-Path $PSScriptRoot "Projeto.Relatorio.psm1"
Import-Module $relatorioModule -Force -DisableNameChecking -ErrorAction Stop

function Invoke-ProjetoCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Titulo,

        [Parameter(Mandatory)]
        [scriptblock]$Comando,

        [string]$Relatorio,

        [switch]$PermitirFalha,

        [switch]$OcultarComando
    )

    Write-ProjetoSecao -Titulo $Titulo -Relatorio $Relatorio

    if (-not $OcultarComando) {
        Write-ProjetoLog -Mensagem ("COMANDO: {0}" -f $Comando.ToString().Trim()) -Relatorio $Relatorio -SemPrefixo
        Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio -SemPrefixo
    }

    $errorActionAnterior = $ErrorActionPreference
    $nativePreferenceDisponivel = Test-Path variable:PSNativeCommandUseErrorActionPreference
    $nativePreferenceAnterior = $null

    if ($nativePreferenceDisponivel) {
        $nativePreferenceAnterior = $PSNativeCommandUseErrorActionPreference
    }

    $saida = @()
    $codigo = 0
    $excecao = $null

    try {
        $ErrorActionPreference = "Continue"

        if ($nativePreferenceDisponivel) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $global:LASTEXITCODE = 0
        $saida = @(& $Comando 2>&1)
        $codigo = [int]$global:LASTEXITCODE
    }
    catch {
        $excecao = $_
        $saida += $_
        $codigo = 1
    }
    finally {
        $ErrorActionPreference = $errorActionAnterior

        if ($nativePreferenceDisponivel) {
            $PSNativeCommandUseErrorActionPreference = $nativePreferenceAnterior
        }
    }

    foreach ($item in $saida) {
        if ($null -eq $item) {
            continue
        }

        $texto = ($item | Out-String).TrimEnd()

        if (-not [string]::IsNullOrEmpty($texto)) {
            Write-ProjetoLog -Mensagem $texto -Relatorio $Relatorio -SemPrefixo
        }
    }

    Write-ProjetoResultado -Titulo $Titulo -ExitCode $codigo -Relatorio $Relatorio

    $resultado = [pscustomobject]@{
        Titulo = $Titulo
        ExitCode = $codigo
        Sucesso = ($codigo -eq 0)
        Saida = $saida
        Excecao = $excecao
    }

    if (($codigo -ne 0) -and (-not $PermitirFalha)) {
        throw "Falha no comando '{0}'. Exit code: {1}" -f $Titulo, $codigo
    }

    return $resultado
}

function Test-ProjetoRaizDjango {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Caminho
    )

    $raiz = (Resolve-Path -LiteralPath $Caminho -ErrorAction Stop).Path

    if (-not (Test-Path -LiteralPath (Join-Path $raiz "manage.py") -PathType Leaf)) {
        throw "manage.py nao encontrado em: $raiz"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $raiz ".git") -PathType Container)) {
        throw "Repositorio Git nao encontrado em: $raiz"
    }

    return $raiz
}

Export-ModuleMember -Function `
    Invoke-ProjetoCommand, `
    Test-ProjetoRaizDjango
