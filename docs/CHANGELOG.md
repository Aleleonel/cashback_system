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