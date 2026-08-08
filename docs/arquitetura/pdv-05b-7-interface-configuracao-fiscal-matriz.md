# PDV-05B.7 — Interface Operacional da Configuração Fiscal da Matriz

## Objetivo

Disponibilizar no ERP uma tela operacional para configurar os parâmetros fiscais da matriz sem depender do Django Admin.

## Arquitetura

A interface reutiliza o model, form e services existentes.

Foi criado um selector administrativo separado para recuperar a configuração da matriz mesmo quando ela estiver inativa.

O selector operacional usado pelo Motor Fiscal permanece inalterado e continua retornando apenas configurações ativas.

## Segurança

A rota exige autenticação e `fiscal.configurar`.

A matriz vem do contexto operacional e não é editável no formulário.

## Fluxo

- GET sem configuração: formulário para criação.
- GET com configuração: formulário preenchido.
- POST sem configuração: service de criação.
- POST com configuração: service de atualização.
- Sucesso: Post/Redirect/Get para a própria tela.
