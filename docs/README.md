# Cashback System

Sistema SaaS multiempresa para gestao de clientes, cashback, campanhas, vouchers e relatorios.

## Estrutura principal

- Plataforma: administracao do SaaS pelo superuser.
- Matriz: empresa cliente.
- Loja: unidade operacional vinculada a uma matriz.
- Usuario operacional: usuario vinculado a uma matriz e uma ou mais lojas.

## Contextos do sistema

### Plataforma

Acesso exclusivo para `is_superuser=True`.

O superuser nao deve estar vinculado a matriz ou loja.

Acessa:

- Painel Master
- Nova Empresa
- Matrizes
- Lojas
- Auditoria
- Django Admin

### Operacao

Acesso para usuarios vinculados a uma matriz.

Acessa:

- Dashboard
- Clientes
- Cashback
- Campanhas
- Vouchers
- Relatorios

## Validacao obrigatoria

Antes de qualquer commit ou merge:

python manage.py check
python manage.py test

## Estado atual

- RBAC implementado.
- Painel Master implementado.
- Auditoria inicial implementada.
- Wizard Nova Empresa implementado.
- StatusOperacional centralizado em core/choices.py.
- Matriz e Loja usam status como fonte unica da verdade.
