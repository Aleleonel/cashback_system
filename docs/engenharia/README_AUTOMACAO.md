# Framework de Automacao - Cashback System

## Objetivo

Padronizar diagnosticos, validacoes, aplicacoes, backups, rollback, testes, Git e relatorios.

## Estrutura

- `scripts/lib/Projeto.Automacao.psm1`
- `scripts/lib/Projeto.Relatorio.psm1`
- `scripts/lib/Projeto.Git.psm1`
- `scripts/lib/Projeto.Testes.psm1`
- `scripts/lib/Projeto.Backup.psm1`
- `scripts/lib/Projeto.Diagnostico.psm1`
- `scripts/Projeto.Config.psd1`
- `scripts/templates/`

## Instalacao

Extraia este pacote na raiz do projeto, onde esta o `manage.py`.

Execute:

```powershell
Unblock-File .\52_instalar_validar_framework_automacao_ASCII.ps1
.\52_instalar_validar_framework_automacao_ASCII.ps1
```

## Regras

1. Diagnosticos sao somente leitura.
2. Aplicacoes declaram previamente todos os arquivos que podem alterar.
3. Aplicacoes criam backup antes de modificar arquivos.
4. Falhas de validacao devem disparar rollback.
5. Commits usam staging seletivo.
6. Warnings de Git e mensagens normais do Django nao sao tratados como falha.
7. A decisao de sucesso ou falha usa o exit code real.

## Motor de patch

O motor de patch estrutural sera implementado como a proxima entrega da Sprint 0.
Ele nao foi misturado nesta primeira base para evitar que uma camada ainda nao validada altere codigo-fonte.
