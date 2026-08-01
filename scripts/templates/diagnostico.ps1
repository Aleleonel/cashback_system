param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$automacao = Join-Path $ProjectRoot "scripts\lib\Projeto.Automacao.psm1"
Import-Module $automacao -Force
Import-ProjetoFramework -Raiz $ProjectRoot

$ProjectRoot = Test-ProjetoRaizDjango -Caminho $ProjectRoot
Set-Location -LiteralPath $ProjectRoot

$relatorio = New-ProjetoRelatorio `
    -Prefixo "diagnostico_EXEMPLO" `
    -Diretorio (Join-Path $ProjectRoot "relatorios")

Write-ProjetoSecao -Titulo "DIAGNOSTICO - EXEMPLO" -Relatorio $relatorio
Write-ProjetoLog -Mensagem ("PROJETO: " + $ProjectRoot) -Relatorio $relatorio -SemPrefixo
Write-ProjetoLog -Mensagem ("BRANCH: " + (Get-ProjetoGitBranch)) -Relatorio $relatorio -SemPrefixo
Write-ProjetoLog -Mensagem "MODO: SOMENTE LEITURA" -Relatorio $relatorio -SemPrefixo

Invoke-ProjetoCommand `
    -Titulo "STATUS GIT" `
    -Relatorio $relatorio `
    -Comando {
        git status --short
    } | Out-Null

Invoke-DjangoCheck -Relatorio $relatorio | Out-Null

Write-ProjetoLog -Mensagem ("RELATORIO: " + $relatorio) -Relatorio $relatorio -SemPrefixo
