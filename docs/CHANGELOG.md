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
