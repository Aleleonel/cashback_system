param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $ProjectRoot "scripts\lib\Projeto.Automacao.psm1") -Force
Import-ProjetoFramework -Raiz $ProjectRoot

$ProjectRoot = Test-ProjetoRaizDjango -Caminho $ProjectRoot
Set-Location -LiteralPath $ProjectRoot

$relatorio = New-ProjetoRelatorio `
    -Prefixo "validacao_EXEMPLO" `
    -Diretorio (Join-Path $ProjectRoot "relatorios")

Invoke-DjangoCheck -Relatorio $relatorio | Out-Null
Test-ProjetoGitDiff -Relatorio $relatorio | Out-Null

Write-ProjetoLog -Mensagem ("VALIDACAO CONCLUIDA: " + $relatorio) -Relatorio $relatorio -SemPrefixo
