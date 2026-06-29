# Segurança

## Objetivo

Garantir confidencialidade, integridade, disponibilidade e rastreabilidade dos dados.

O Cashback System foi desenvolvido seguindo os princípios da LGPD e do menor privilégio.

## Autenticação

Toda área protegida utiliza:

- login obrigatório;
- sessão autenticada;
- proteção CSRF;
- controle de permissões.

Padrão:

@login_required

## Autorização

O sistema utiliza RBAC (Role Based Access Control).

As permissões ficam centralizadas em:

accounts/permissions.py

e são aplicadas através do decorator:

@require_permission()

## Contextos

Existem dois contextos independentes.

### Plataforma

Exclusivo para superusuários.

Características:

- Painel Master
- Auditoria Global
- Matrizes
- Lojas
- Wizard Nova Empresa
- Django Admin

O superusuário não depende de Matriz nem Loja.

### Operação

Usuários operacionais devem possuir:

- Matriz válida;
- Loja válida;
- Permissões compatíveis;
- Status operacional ativo.

## Isolamento entre empresas

Cada Matriz representa um tenant.

Nenhum usuário operacional pode acessar dados de outra matriz.

Toda consulta operacional deve utilizar a matriz do contexto.

## Dados protegidos

Dados considerados sensíveis:

- CPF
- CNPJ
- Nome
- Telefone
- E-mail
- Data de nascimento
- Histórico de compras
- Saldo de cashback

## Auditoria

Toda operação crítica deve gerar auditoria.

Exemplos:

- criação;
- edição;
- exclusão lógica;
- implantação de empresa;
- alteração de status;
- registro de compras;
- campanhas.

## Wizard Nova Empresa

A implantação utiliza:

transaction.atomic()

Se qualquer etapa falhar:

- nenhum registro permanece salvo;
- toda operação é revertida.

## Senhas

Regras:

- nunca registrar senha na auditoria;
- nunca exibir senha na revisão;
- remover senha da sessão após implantação;
- utilizar hash padrão do Django.

## Produção

Obrigatório:

- DEBUG=False
- SECRET_KEY por variável de ambiente
- HTTPS
- Cookies seguros
- CSRF habilitado
- Backup periódico
- Logs persistentes

## Revisão de Segurança

Antes de cada release verificar:

- permissões;
- isolamento entre matrizes;
- auditoria;
- testes;
- consultas protegidas.
