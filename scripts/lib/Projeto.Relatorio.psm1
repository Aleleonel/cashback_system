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

        [ValidateSet("INFO", "SUCESSO", "AVISO", "ERRO", "DEBUG")]
        [string]$Nivel = "INFO",

        [switch]$SemPrefixo
    )

    $texto = if ($SemPrefixo -or [string]::IsNullOrEmpty($Mensagem)) {
        $Mensagem
    }
    else {
        "[{0}] {1}" -f $Nivel, $Mensagem
    }

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
    Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio -SemPrefixo
    Write-ProjetoLog -Mensagem $linha -Relatorio $Relatorio -SemPrefixo
    Write-ProjetoLog -Mensagem $Titulo -Relatorio $Relatorio -SemPrefixo
    Write-ProjetoLog -Mensagem $linha -Relatorio $Relatorio -SemPrefixo
}

function Write-ProjetoResultado {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Titulo,

        [Parameter(Mandatory)]
        [int]$ExitCode,

        [string]$Relatorio
    )

    $resultado = if ($ExitCode -eq 0) { "SUCESSO" } else { "FALHA" }

    Write-ProjetoLog -Mensagem "" -Relatorio $Relatorio -SemPrefixo
    Write-ProjetoLog -Mensagem ("EXIT CODE: {0}" -f $ExitCode) -Relatorio $Relatorio -SemPrefixo
    Write-ProjetoLog -Mensagem ("RESULTADO: {0}" -f $resultado) -Relatorio $Relatorio -SemPrefixo
}

Export-ModuleMember -Function `
    New-ProjetoRelatorio, `
    Write-ProjetoLog, `
    Write-ProjetoSecao, `
    Write-ProjetoResultado
