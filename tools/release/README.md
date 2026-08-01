# Pipeline de Release

Estrutura oficial de diagnóstico, validação, release e rollback do Cashback System.

## Fluxo

1. `01_diagnostico.ps1`
2. `02_validacao.ps1`
3. `03_release.ps1`
4. `04_rollback.ps1`

## Regras

- executar na raiz do repositório;
- manter o ambiente virtual ativo;
- não usar `push --force`;
- validar Django, migrations e testes antes do merge;
- preservar uma referência de segurança antes da release;
- não incluir diagnósticos, relatórios de execução ou backups nos commits.

Os scripts desta pasta fazem parte da infraestrutura oficial do projeto.
