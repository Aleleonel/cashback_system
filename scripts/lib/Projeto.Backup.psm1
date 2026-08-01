Set-StrictMode -Version Latest

function New-ProjetoBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Nome,

        [Parameter(Mandatory)]
        [string[]]$Arquivos,

        [string]$DiretorioBase = ".\backups"
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $destino = Join-Path $DiretorioBase ("{0}_{1}" -f $Nome, $timestamp)
    $arquivosDir = Join-Path $destino "arquivos"

    New-Item -ItemType Directory -Path $arquivosDir -Force | Out-Null

    $manifest = [ordered]@{
        nome = $Nome
        criado_em = (Get-Date).ToString("o")
        raiz = (Get-Location).Path
        arquivos = @()
    }

    foreach ($arquivo in $Arquivos) {
        $existe = Test-Path -LiteralPath $arquivo -PathType Leaf

        $entrada = [ordered]@{
            caminho = $arquivo
            existia = $existe
        }

        if ($existe) {
            $destinoArquivo = Join-Path $arquivosDir $arquivo
            $destinoPai = Split-Path -Parent $destinoArquivo

            if (-not (Test-Path -LiteralPath $destinoPai)) {
                New-Item -ItemType Directory -Path $destinoPai -Force | Out-Null
            }

            Copy-Item -LiteralPath $arquivo -Destination $destinoArquivo -Force
        }

        $manifest.arquivos += $entrada
    }

    $manifestPath = Join-Path $destino "manifest.json"
    $manifest | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $manifestPath -Encoding utf8

    return [pscustomobject]@{
        Diretorio = $destino
        Manifesto = $manifestPath
    }
}

function Restore-ProjetoBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$DiretorioBackup
    )

    $manifestPath = Join-Path $DiretorioBackup "manifest.json"

    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Manifesto nao encontrado: $manifestPath"
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $arquivosDir = Join-Path $DiretorioBackup "arquivos"

    foreach ($entrada in $manifest.arquivos) {
        $caminho = [string]$entrada.caminho
        $existia = [bool]$entrada.existia
        $origem = Join-Path $arquivosDir $caminho

        if ($existia) {
            $pai = Split-Path -Parent $caminho

            if ($pai -and (-not (Test-Path -LiteralPath $pai))) {
                New-Item -ItemType Directory -Path $pai -Force | Out-Null
            }

            Copy-Item -LiteralPath $origem -Destination $caminho -Force
        }
        elseif (Test-Path -LiteralPath $caminho) {
            Remove-Item -LiteralPath $caminho -Force
        }
    }
}

Export-ModuleMember -Function `
    New-ProjetoBackup, `
    Restore-ProjetoBackup
