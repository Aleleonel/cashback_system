# Testes

## Objetivo

Garantir que toda funcionalidade nova seja entregue sem regressões.

Nenhuma Sprint pode ser considerada concluída sem validação automática e manual.

## Fluxo obrigatório

Após qualquer implementação executar:

python manage.py test

python manage.py check

## Testes automatizados

Toda nova funcionalidade deve possuir testes quando envolver:

- regras de negócio;
- permissões;
- auditoria;
- implantação;
- cadastro;
- alterações de status;
- integração entre módulos.

## Testes manuais

Além dos testes automatizados, validar manualmente:

- navegação entre telas;
- mensagens de sucesso;
- mensagens de erro;
- formulários;
- filtros;
- paginação;
- permissões;
- auditoria.

## Checklist antes do Commit

Confirmar:

[ ] Todos os testes passaram.

[ ] python manage.py check sem erros.

[ ] Fluxo manual validado.

[ ] Sem erros no console.

[ ] Sem consultas N+1 identificadas.

[ ] Auditoria funcionando.

[ ] Permissões revisadas.

[ ] Sem regressão em funcionalidades existentes.

## Checklist antes do Push

Executar:

python manage.py test

python manage.py check

Revisar:

- imports não utilizados;
- código comentado;
- prints de depuração;
- TODOs esquecidos.

## Política de qualidade

Nenhum commit deve:

- quebrar testes;
- reduzir segurança;
- remover auditoria;
- gerar regressão.

## Cobertura

Dar prioridade para testes de:

- Services
- Selectors
- Permissões
- Wizard Nova Empresa
- Cadastro de Clientes
- Cashback
- Campanhas
- Auditoria

Views simples devem ser testadas principalmente pelo fluxo funcional.

## Objetivo

Toda versão enviada ao cliente deve estar em estado potencialmente implantável.
