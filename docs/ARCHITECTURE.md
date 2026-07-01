# Arquitetura do Cashback System

## Visao geral

O Cashback System e um SaaS multiempresa construido em Django.

A arquitetura separa claramente dois contextos:

- Plataforma: administracao do produto SaaS.
- Operacao: uso diario por empresas clientes.

## Plataforma

A Plataforma e acessada apenas por usuarios `is_superuser=True`.

Responsabilidades:

- Painel Master.
- Wizard Nova Empresa.
- Cadastro de matrizes.
- Cadastro de lojas.
- Auditoria global.
- Django Admin.

O superuser nao deve depender de matriz ou loja.

## Operacao

A Operacao e acessada por usuarios vinculados a uma matriz e a uma ou mais lojas.

Responsabilidades:

- Dashboard operacional.
- Clientes.
- Compras.
- Cashback.
- Vouchers.
- Campanhas.
- Relatorios.

## Multiempresa

Cada matriz representa um tenant.

Regras obrigatorias:

- Dados operacionais devem sempre ser filtrados por matriz.
- Usuarios operacionais acessam somente dados da propria matriz.
- Superuser acessa a plataforma, nao o contexto operacional.

## Camadas

Padrao recomendado:

URL -> View -> Decorator -> Service -> Selector -> Model -> Template

## Views

Responsaveis por:

- Receber request.
- Validar forms.
- Chamar services e selectors.
- Renderizar templates.
- Redirecionar.

Views nao devem conter regra de negocio complexa.

## Services

Responsaveis por regras de negocio e escrita no banco.

Exemplos:

- implantar_empresa
- registrar_auditoria
- registrar_compra
- registrar_disparos_aniversariantes

## Selectors

Responsaveis por consultas otimizadas.

Devem considerar:

- select_related
- prefetch_related
- annotate
- only
- paginacao

## Models

Responsaveis por representar dominio e persistencia.

## Status operacional

O status operacional fica centralizado em:

core/choices.py

Fonte unica da verdade:

StatusOperacional

Usado por:

- Matriz
- Loja

Nao usar campos booleanos como `ativa` para representar ciclo de vida operacional.

## Wizard Nova Empresa

O Wizard cria:

- Matriz
- Loja principal
- Usuario administrador da matriz
- Configuracao inicial
- Auditoria

A implantacao deve ser transacional com transaction.atomic().

Se uma etapa falhar, nada deve ser persistido parcialmente.


# Sprint 15

## Organização

empresa/

    views/
        dashboard.py
        lojas.py
        usuarios.py
        auditoria.py
        configuracoes.py

templates/

    partials/
        sidebar.html
        navbar.html

---

## Princípios

Cada funcionalidade segue o padrão:

Permissão
→ Selector
→ Service
→ View
→ Template
→ Sidebar
→ Auditoria
→ Testes

---

## Decisões arquiteturais

- Sidebar controlada por permissões.
- Serviços responsáveis por regras de negócio.
- Selectors responsáveis por consultas.
- Auditoria desacoplada das views.
- Permissões extras desacopladas do perfil.
- Componentização de templates.

---

## Melhorias registradas

Para versões futuras:

- Separação de ConfiguracaoSistema em módulos.
- Sidebar construída dinamicamente.
- Sistema de plugins.
- Jobs assíncronos.
- Cache.
- API pública.