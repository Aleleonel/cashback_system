param(
    [Parameter(Mandatory)]
    [string[]]$Arquivos,

    [Parameter(Mandatory)]
    [string]$Mensagem,

    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $ProjectRoot "scripts\lib\Projeto.Automacao.psm1") -Force
Import-ProjetoFramework -Raiz $ProjectRoot

$ProjectRoot = Test-ProjetoRaizDjango -Caminho $ProjectRoot
Set-Location -LiteralPath $ProjectRoot

$relatorio = New-ProjetoRelatorio `
    -Prefixo "validacao_commit" `
    -Diretorio (Join-Path $ProjectRoot "relatorios")

Invoke-DjangoCheck -Relatorio $relatorio | Out-Null
Test-ProjetoGitDiff -Relatorio $relatorio | Out-Null
Add-ProjetoArquivos -Arquivos $Arquivos -Relatorio $relatorio | Out-Null

Invoke-ProjetoCommand `
    -Titulo "PREVIEW DO STAGING" `
    -Relatorio $relatorio `
    -Comando {
        git diff --cached --stat
        git diff --cached --name-status
    } | Out-Null

$confirmacao = Read-Host "Digite COMMIT para confirmar"

if ($confirmacao -cne "COMMIT") {
    throw "Commit cancelado pelo usuario."
}

Commit-Projeto -Mensagem $Mensagem -Relatorio $relatorio | Out-Null

Write-ProjetoLog -Mensagem ("COMMIT CONCLUIDO: " + $relatorio) -Relatorio $relatorio -SemPrefixo
