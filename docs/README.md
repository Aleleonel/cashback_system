# Cashback System

Sistema SaaS multiempresa para gestão de clientes, cashback, campanhas, vouchers e relatórios.

## Estrutura principal

- Plataforma: gestão do SaaS pelo superuser.
- Matriz: empresa cliente.
- Loja: unidade vinculada à matriz.

## Validação obrigatória

Antes de qualquer merge:

```bash
python manage.py check
python manage.py test