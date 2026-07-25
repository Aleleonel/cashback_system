# Pipeline de Release — Cashback System

Estrutura:

```text
tools/
└── release/
    ├── 01_diagnostico.ps1
    ├── 02_validacao.ps1
    ├── 03_release.ps1
    ├── 04_rollback.ps1
    └── README.md
```

## Requisitos

- Windows PowerShell 5.1
- Git disponível no terminal
- ambiente virtual Python ativado
- execução feita dentro do repositório
- branch de feature correta selecionada

## Fluxo recomendado

### 1. Diagnóstico

```powershell
.\tools\release\01_diagnostico.ps1 -TargetBranch develop
```

Não altera commits ou branches.

### 2. Validação

Para apps específicos:

```powershell
.\tools\release\02_validacao.ps1 -TestApps rh,compras
```

Para a suíte completa:

```powershell
.\tools\release\02_validacao.ps1 -FullTestSuite
```

### 3. Release

Exemplo para concluir o RH:

```powershell
.\tools\release\03_release.ps1 `
  -FeatureBranch "feature/rh-02-cadastro-cargos" `
  -TargetBranch "develop" `
  -CommitMessage "feat(ui): conclui padronizacao visual de pedidos de compra" `
  -MergeMessage "merge: incorpora modulo RH e consolidacao visual na develop" `
  -TestApps rh,compras
```

O script:

1. atualiza referências remotas;
2. ignora somente artefatos temporários conhecidos;
3. cria patch de backup;
4. executa validações;
5. commita alterações relevantes;
6. envia a feature;
7. atualiza a branch de destino;
8. cria uma tag local de segurança;
9. executa merge `--no-ff`;
10. repete as validações;
11. envia a branch de destino.

## Artefatos ignorados

O pipeline ignora:

```text
diagnosticos/
tools/diagnostics/
__pycache__/
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage
coverage.xml
*.pyc
*.pyo
*.log
*.tmp
```

Eles não entram automaticamente no commit.

## Rollback

O rollback é apenas local e não usa `push --force`.

```powershell
.\tools\release\04_rollback.ps1 `
  -SafetyTag "safety/pre-merge-feature-rh-02-cadastro-cargos-AAAAMMDD_HHMMSS" `
  -TargetBranch develop
```

Antes de restaurar, ele cria uma branch de backup com o estado atual.

## Recomendação para o `.gitignore`

Adicionar, caso ainda não estejam presentes:

```gitignore
diagnosticos/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage
coverage.xml
*.log
*.tmp
```

## Observação importante

Tags de segurança são criadas localmente. O pipeline não envia tags automaticamente ao remoto.
