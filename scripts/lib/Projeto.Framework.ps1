Set-StrictMode -Version Latest

function New-ProjetoRelatorio {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Prefixo,

        [string]$Diretorio = (Get-Location).Path
    )

    if (-not (Test-Path -LiteralPath $Diretorio -PathType Container)) {
        New-Item -ItemType Directory -Path $Diretorio -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    return Join-Path $Diretorio ("{0}_{1}.txt" -f $Prefixo, $timestamp)
}

function Write-ProjetoLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Mensagem,

        [string]$Relatorio,

        [switch]$SemPrefixo
    )

    $texto = $Mensagem
    Write-Host $texto

    if (-not [string]::IsNullOrWhiteSpace($Relatorio)) {
        $texto | Out-File -LiteralPath $Relatorio -Append -Encoding utf8
    }
}

function Write-ProjetoSecao {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Titulo,

        [string]$Relatorio,

        [int]$Largura = 110
    )

    $linha = "=" * $Largura
    Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem $linha -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem $Titulo -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem $linha -Relatorio $Relatorio
}

function Write-ProjetoResultado {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [int]$ExitCode,

        [string]$Relatorio
    )

    $resultado = if ($ExitCode -eq 0) { "SUCESSO" } else { "FALHA" }

    Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem ("EXIT CODE: {0}" -f $ExitCode) -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem ("RESULTADO: {0}" -f $resultado) -Relatorio $Relatorio
}

function Invoke-ProjetoCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Titulo,

        [Parameter(Mandatory)]
        [scriptblock]$Comando,

        [string]$Relatorio,

        [switch]$PermitirFalha
    )

    Write-ProjetoSecao -Titulo $Titulo -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem ("COMANDO: {0}" -f $Comando.ToString().Trim()) -Relatorio $Relatorio
    Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio

    $errorActionAnterior = $ErrorActionPreference
    $nativeExiste = Test-Path variable:PSNativeCommandUseErrorActionPreference
    $nativeAnterior = $null

    if ($nativeExiste) {
        $nativeAnterior = $PSNativeCommandUseErrorActionPreference
    }

    $saida = @()
    $codigo = 0

    try {
        $ErrorActionPreference = "Continue"

        if ($nativeExiste) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $global:LASTEXITCODE = 0
        $saida = @(& $Comando 2>&1)
        $codigo = [int]$global:LASTEXITCODE
    }
    catch {
        $saida += $_
        $codigo = 1
    }
    finally {
        $ErrorActionPreference = $errorActionAnterior

        if ($nativeExiste) {
            $PSNativeCommandUseErrorActionPreference = $nativeAnterior
        }
    }

    foreach ($item in $saida) {
        if ($null -eq $item) {
            continue
        }

        $texto = ($item | Out-String).TrimEnd()

        if (-not [string]::IsNullOrEmpty($texto)) {
            Write-ProjetoLog -Mensagem $texto -Relatorio $Relatorio
        }
    }

    Write-ProjetoResultado -ExitCode $codigo -Relatorio $Relatorio

    $resultado = [pscustomobject]@{
        Titulo = $Titulo
        ExitCode = $codigo
        Sucesso = ($codigo -eq 0)
        Saida = $saida
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

function Get-ProjetoGitBranch {
    [CmdletBinding()]
    param()

    $saida = @(& git branch --show-current 2>$null)
    $codigo = $LASTEXITCODE

    if ($codigo -ne 0) {
        throw "Nao foi possivel identificar a branch atual."
    }

    return (($saida | Out-String).Trim())
}

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
