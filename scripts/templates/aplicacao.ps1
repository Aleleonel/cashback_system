param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $ProjectRoot "scripts\lib\Projeto.Automacao.psm1") -Force
Import-ProjetoFramework -Raiz $ProjectRoot

$ProjectRoot = Test-ProjetoRaizDjango -Caminho $ProjectRoot
Set-Location -LiteralPath $ProjectRoot

$arquivos = @(
    # Liste aqui somente os arquivos que a aplicacao pode alterar.
)

if ($arquivos.Count -eq 0) {
    throw "Nenhum arquivo foi declarado para a aplicacao."
}

$backup = New-ProjetoBackup -Nome "aplicacao_EXEMPLO" -Arquivos $arquivos

try {
    # Aplicar alteracoes aqui.

    Invoke-DjangoCheck | Out-Null
}
catch {
    Restore-ProjetoBackup -DiretorioBackup $backup.Diretorio
    throw
}
