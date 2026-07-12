# Changelog

## 2026-06-29

### Segurança

- Bloqueado acesso do superuser ao contexto operacional.
- Adicionados testes para impedir acesso direto do superuser às URLs operacionais.
- Aplicado RBAC nas views de Clientes.
- Aplicado RBAC na Nova Compra.
- Aplicado RBAC nas views operacionais de Campanhas.
- Aplicado RBAC no Dashboard Operacional.
- Organizadas permissões por módulo em `accounts/permissions.py`.
- Adicionada auditoria automática para tentativas de acesso negado.

### Plataforma

- Wizard Nova Empresa implementado.
- Implantação de empresa com transação atômica.
- Matriz e Loja padronizadas com `StatusOperacional`.

### Documentação

- Atualizados README, Arquitetura, Segurança e Testes.

# Changelog

## Sprint 15 - Empresa e Permissões Extras

### Adicionado

- Painel da Empresa para administradores da matriz.
- CRUD completo de lojas da empresa.
- Configuração operacional de cashback por matriz.
- CRUD de usuários da empresa.
- Vínculo de usuários a múltiplas lojas.
- Permissões extras por usuário.
- Auditoria das operações da empresa.
- Sidebar modularizada em partials.
- Sidebar dinâmica baseada em RBAC.
- Context Processor para disponibilizar permissões aos templates.

### Segurança

- Permissões extras passam a complementar as permissões do perfil.
- Admin da matriz pode delegar funcionalidades específicas sem promover o usuário para administrador.

### Refatoração

- Separação de navbar e sidebar em componentes reutilizáveis.
- Organização das views da empresa por responsabilidade.
- Organização dos serviços da empresa.

- Cria estrutura padrão para JavaScript por módulo.
- Cria estrutura padrão para CSS por módulo.
- Adiciona diretórios shared para reutilização de código.
- Prepara arquitetura frontend para modularização.
- Nenhuma alteração funcional.

## Sprint 17.6

### Arquitetura Frontend

- Padronizada estrutura de assets JavaScript.
- Padronizada estrutura de assets CSS.
- Criado diretório shared para componentes reutilizáveis.
- Criada estrutura modular por aplicação.
- Preparação para modularização completa do frontend.

Status:
- Sem alterações funcionais.
- Compatibilidade total com a implementação atual.

## [Unreleased]

### Added

- Novo extrato financeiro baseado em movimentações.
- Resumo financeiro do cliente.
- Cashback sobre valor líquido.
- Voucher e cashback mutuamente exclusivos.
- Cashback parcial.
- Melhorias na experiência do operador do caixa.
- Nova arquitetura para movimentações financeiras.

Sprint 26
História: H006

Status:
✔ Concluída

Entregas

✔ Chave de idempotência
✔ Constraint UNIQUE
✔ Migração dos registros antigos
✔ Service protegida
✔ View protegida
✔ Auditoria protegida
✔ Cashback protegido
✔ Voucher protegido
✔ Botão anti duplo clique
✔ Feedback visual
✔ Teste automatizado
✔ 63 testes passando

Resumo da Sprint 26 (até o momento)

Hoje concluímos:

✅ H006 – Idempotência da venda
Chave UUID por operação
Proteção contra duplo clique
Constraint unique
Migração para dados existentes
Tratamento de concorrência
✅ H007 – Regra de benefícios
Cashback OU Voucher
Nunca ambos simultaneamente
Backend, API e Frontend alinhados
Novos testes automatizados
✅ H008 – Concorrência do cliente
select_for_update() para clientes existentes
Eliminação de condição de corrida na atualização cadastral
Fluxo transacional fortalecido

E tudo isso mantendo:

✅ git diff --check
✅ python manage.py check
✅ 65 testes passando
✅ homologação manual
✅ commits organizados
✅ push realizado
