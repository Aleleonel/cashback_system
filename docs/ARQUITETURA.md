# Arquitetura do Cashback System

## Objetivo

O Cashback System deve evoluir como um sistema comercial modular,
multiempresa, auditável, testável e preparado para crescimento.

## Princípios obrigatórios

### Arquitetura em camadas

O fluxo padrão é:

View
  -> Form
  -> Service
  -> Selector
  -> Model

- Views recebem requisições e devolvem respostas.
- Forms validam entradas de interface.
- Services executam regras de negócio e gravações.
- Selectors concentram consultas.
- Models representam persistência e invariantes.
- Templates não executam regras de negócio.

### Isolamento multiempresa

Toda consulta e gravação operacional deve estar vinculada à matriz correta.
Registros de outra matriz não podem ser expostos por URL, formulário, selector ou service.

### Auditoria

Criações, edições, importações, alterações financeiras e acessos negados relevantes devem gerar registros de auditoria.

### Testes

- python manage.py check
- python manage.py makemigrations --check --dry-run
- testes específicos
- suíte completa sem regressões

## Infraestrutura compartilhada

Nenhum domínio deve criar infraestrutura própria quando existir uma solução genérica reutilizável.

## Motor de importação

A infraestrutura compartilhada está localizada em core/importacao/.

Fluxo padrão:

Upload
  -> Validação
  -> Pré-visualização
  -> Confirmação
  -> Transação
  -> Auditoria

Nenhuma importação deve gravar dados durante a etapa de validação.

## Evolução prevista

Importações grandes deverão futuramente usar uma entidade persistente de processamento,
guardando na sessão apenas o identificador da importação.
