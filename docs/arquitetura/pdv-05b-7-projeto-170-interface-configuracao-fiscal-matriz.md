# PDV-05B.7 — Projeto 170
## Interface Operacional da Configuração Fiscal da Matriz

### 1. Objetivo

Criar a tela operacional da **Configuração Fiscal da Matriz** dentro do módulo Fiscal, reutilizando integralmente o backend já existente.

A sprint não deve recriar model, migration, form, selector ou regras de negócio. A implementação será apenas a camada operacional de interface: rota, view, template, integração com a Central Fiscal, permissões e testes de UI/fluxo.

---

### 2. Premissas confirmadas pelo Diagnóstico 169C

Já existem e devem ser reutilizados:

- `ConfiguracaoFiscalMatriz`;
- `ConfiguracaoFiscalMatrizForm`;
- `get_configuracao_fiscal_matriz`;
- `criar_configuracao_fiscal_matriz`;
- `atualizar_configuracao_fiscal_matriz`;
- auditoria de criação e atualização;
- migration `0023_configuracao_fiscal_matriz`;
- testes de model, form, selector e services;
- Central Fiscal;
- sistema de permissões Fiscal.

Não será criada nova migration nesta sprint, salvo se uma validação posterior comprovar necessidade real.

---

### 3. Regra arquitetural

Fluxo obrigatório:

```text
Usuário
  ↓
Central Fiscal
  ↓
Configuração Fiscal da Matriz
  ↓
View operacional
  ↓
ConfiguracaoFiscalMatrizForm
  ↓
Service existente
  ↓
ConfiguracaoFiscalMatriz
  ↓
Auditoria
```

A view não deve:

- fazer `Model.objects.create()` diretamente;
- fazer `configuracao.save()` diretamente;
- duplicar validações de UF;
- duplicar regra de unicidade por matriz;
- duplicar auditoria;
- alterar o Motor Fiscal;
- alterar o Painel Fiscal do Produto.

---

### 4. Permissões

Usar as permissões já existentes:

- leitura/entrada na Central Fiscal: `PERMISSAO_FISCAL_VISUALIZAR`;
- configuração da matriz: `PERMISSAO_FISCAL_CONFIGURAR`.

A nova tela **não deve usar** `PERMISSAO_FISCAL_GERENCIAR_CADASTROS` como permissão principal, porque já existe uma permissão específica denominada **Configurar parâmetros fiscais**.

Fluxo:

```text
GET/POST Configuração Fiscal da Matriz
→ login_required
→ require_permission(PERMISSAO_FISCAL_CONFIGURAR)
```

---

### 5. Escopo de matriz

A configuração operacional deve sempre pertencer à matriz do contexto operacional do usuário.

A matriz:

- não será selecionada manualmente no formulário;
- não será enviada em campo editável;
- será obtida pelo contexto operacional;
- será passada ao service na criação;
- será usada para localizar a configuração existente;
- não poderá ser trocada durante a edição.

Isso preserva isolamento multiempresa/multimatriz.

---

### 6. Comportamento da tela

Será usada uma única rota operacional para criação e edição.

Rota proposta:

```text
/fiscal/configuracao-matriz/
```

Nome:

```python
fiscal:configuracao_fiscal_matriz
```

#### Cenário A — Matriz ainda não possui configuração

A view deve:

1. obter o contexto operacional;
2. identificar a matriz;
3. verificar a configuração existente;
4. instanciar `ConfiguracaoFiscalMatrizForm`;
5. no POST válido chamar `criar_configuracao_fiscal_matriz`;
6. registrar auditoria via service;
7. exibir mensagem de sucesso;
8. redirecionar para a própria tela.

#### Cenário B — Matriz já possui configuração

A view deve:

1. obter a configuração da matriz;
2. carregar o form com `instance=configuracao`;
3. no POST válido chamar `atualizar_configuracao_fiscal_matriz`;
4. registrar auditoria via service;
5. exibir mensagem de sucesso;
6. redirecionar para a própria tela.

---

### 7. Atenção ao selector atual

`get_configuracao_fiscal_matriz()` retorna somente configuração com `ativa=True`.

Para a tela administrativa isso é insuficiente, porque uma configuração inativa deve continuar editável.

Portanto, a Aplicação 170 deve **não usar esse selector para decidir se o registro existe**.

Opções permitidas, em ordem de preferência:

1. adicionar um selector específico de administração, por exemplo:
   `get_configuracao_fiscal_matriz_para_edicao(*, matriz)`,
   que retorne a configuração independentemente de `ativa`;
2. ou ampliar o selector existente com parâmetro explícito, sem alterar o comportamento padrão usado pelo Motor.

Não é permitido mudar silenciosamente o comportamento atual de
`get_configuracao_fiscal_matriz()`, pois o Contexto Tributário depende de ele ignorar configurações inativas.

---

### 8. Campos da interface

O formulário existente deve ser reutilizado com:

- Regime tributário;
- UF de origem;
- Contribuinte do ICMS;
- Consumidor final padrão;
- Ativa;
- Observações.

A Matriz será apresentada apenas como informação contextual, não como campo editável.

---

### 9. Experiência de uso

Cabeçalho sugerido:

```text
Configuração Fiscal da Matriz
Defina os parâmetros fiscais padrão usados pelo Motor Fiscal.
```

Resumo superior:

- Matriz atual;
- situação: Configurada / Não configurada;
- estado: Ativa / Inativa;
- indicação de prontidão para operação.

A tela deve explicar de forma curta:

- Regime tributário: regime fiscal padrão da matriz;
- UF de origem: origem usada pelo contexto tributário;
- Contribuinte do ICMS: valor padrão quando a operação não informar explicitamente;
- Consumidor final padrão: fallback operacional;
- Ativa: somente configurações ativas alimentam o contexto tributário;
- Observações: campo administrativo.

Botão principal:

```text
Salvar configuração
```

Não haverá botão Excluir nesta sprint.

---

### 10. Integração com a Central Fiscal

Adicionar um acesso na Central Fiscal para:

```text
Configuração da Matriz
Parâmetros fiscais usados como base pelo Motor Fiscal.
```

O link deve aparecer apenas quando o usuário puder configurar parâmetros fiscais.

A sidebar principal continuará apontando para a Central Fiscal; não é necessário criar um item adicional na sidebar.

---

### 11. Arquivos previstos

#### Criar

```text
fiscal/views_configuracao_fiscal.py
fiscal/templates/fiscal/configuracao_fiscal_matriz/form.html
fiscal/tests/test_configuracao_fiscal_matriz_ui.py
docs/arquitetura/pdv-05b-7-interface-configuracao-fiscal-matriz.md
docs/usabilidade/fiscal/configuracao-fiscal-matriz-operacional.md
```

#### Alterar

```text
fiscal/urls.py
fiscal/templates/fiscal/inicio.html
```

Possivelmente:

```text
fiscal/selectors_configuracao_fiscal.py
```

somente para criar o selector administrativo que encontre também configuração inativa.

Não alterar:

```text
fiscal/models_configuracao_fiscal.py
fiscal/migrations/0023_configuracao_fiscal_matriz.py
fiscal/services_contexto_tributario.py
produtos/services/fiscal/painel_produto_fiscal.py
produtos/services/fiscal/resolver_produto_fiscal.py
```

---

### 12. Contrato da nova view

Nome sugerido:

```python
configuracao_fiscal_matriz_view(request)
```

Responsabilidades:

1. autenticar;
2. validar `PERMISSAO_FISCAL_CONFIGURAR`;
3. obter `get_contexto_operacional_usuario(request.user)`;
4. extrair `matriz` e `loja`;
5. bloquear operação se não houver matriz;
6. recuperar configuração existente, inclusive inativa;
7. criar o form adequado para GET ou POST;
8. delegar criação/edição aos services existentes;
9. aplicar `ValidationError` ao formulário;
10. apresentar mensagem de sucesso;
11. usar Post/Redirect/Get;
12. renderizar o template.

---

### 13. Tratamento de ValidationError

A view deve seguir o padrão já usado nos cadastros fiscais.

Erros de campo:

```python
erro.message_dict
```

devem ser adicionados ao respectivo campo.

Erros sem campo devem entrar em:

```python
form.add_error(None, ...)
```

A interface não deve transformar falhas de validação do service em erro 500.

---

### 14. Segurança

A implementação deverá provar:

- usuário sem login não acessa;
- usuário sem `fiscal.configurar` não acessa;
- matriz vem do contexto, não do POST;
- configuração de outra matriz não pode ser manipulada;
- configuração inativa continua acessível para reativação;
- não é possível criar duas configurações para a mesma matriz;
- GET não altera dados;
- POST válido usa service;
- auditoria continua sendo registrada pelo service.

---

### 15. Testes obrigatórios

Novo arquivo:

```text
fiscal/tests/test_configuracao_fiscal_matriz_ui.py
```

Cobertura mínima:

1. rota existe;
2. exige autenticação;
3. exige `PERMISSAO_FISCAL_CONFIGURAR`;
4. GET sem configuração retorna 200;
5. GET apresenta matriz do contexto;
6. GET não permite selecionar outra matriz;
7. POST cria configuração;
8. POST usa valores do formulário;
9. criação gera auditoria;
10. segundo acesso carrega configuração existente;
11. POST atualiza configuração;
12. atualização gera auditoria;
13. configuração inativa pode ser aberta;
14. configuração inativa pode ser reativada;
15. UF inválida retorna erro no formulário;
16. duplicidade não gera erro 500;
17. matriz ausente é tratada de forma controlada;
18. usuário de outra matriz não manipula a configuração;
19. Central Fiscal contém acesso à tela;
20. usuário sem permissão de configurar não recebe ação de edição.

---

### 16. Regressão obrigatória

Após implementação:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test fiscal.tests.test_configuracao_fiscal_matriz --verbosity=1
python manage.py test fiscal.tests.test_contexto_tributario --verbosity=1
python manage.py test fiscal.tests.test_configuracao_fiscal_matriz_ui --verbosity=1
python manage.py test fiscal.tests.test_central_fiscal_ui --verbosity=1
```

Depois executar regressão Fiscal completa ou bateria equivalente da sprint.

---

### 17. Critérios de homologação visual

#### Caso 1 — Sem configuração

Acessar Central Fiscal → Configuração da Matriz.

Esperado:

- matriz identificada corretamente;
- formulário vazio;
- campos legíveis;
- botão Salvar;
- nenhuma opção para escolher outra matriz.

#### Caso 2 — Criar

Preencher dados válidos e salvar.

Esperado:

- mensagem de sucesso;
- redirect para a mesma página;
- dados persistidos;
- status Configurada/Ativa;
- Painel Fiscal do Produto deixa de acusar ausência de configuração quando aplicável.

#### Caso 3 — Editar

Alterar um valor e salvar.

Esperado:

- persistência;
- mensagem de sucesso;
- reload com valor atualizado.

#### Caso 4 — Desativar

Desmarcar Ativa e salvar.

Esperado:

- registro continua acessível na tela administrativa;
- status Inativa;
- contexto tributário deixa de utilizar a configuração.

#### Caso 5 — Reativar

Marcar Ativa e salvar.

Esperado:

- registro volta a ser considerado pelo contexto tributário.

#### Caso 6 — UF inválida

Informar `XX`.

Esperado:

- mensagem de validação;
- sem erro 500;
- dados inválidos não persistem.

---

### 18. Fora de escopo

Não fazer nesta sprint:

- cálculo de impostos;
- novas regras fiscais;
- cadastro de NCM/CEST/CST;
- exclusão da configuração;
- múltiplas configurações por matriz;
- configuração por loja;
- histórico próprio de versões;
- alteração do Motor Fiscal;
- alteração do Painel Fiscal do Produto;
- nova migration sem necessidade comprovada.

---

### 19. Decisão arquitetural final

A PDV-05B.7 será uma **camada operacional fina** sobre o backend já homologado.

O ponto novo mais importante é diferenciar:

```text
selector operacional do Motor
→ somente configuração ativa

selector administrativo
→ configuração existente, ativa ou inativa
```

Essa separação evita um defeito importante: uma configuração desativada nunca pode “sumir” da tela administrativa, pois o usuário precisa conseguir reativá-la.

---

### 20. Próxima etapa

Após aprovação deste projeto:

```text
Validação 170
    ↓
Aplicação 170
    ↓
Testes
    ↓
Homologação visual
    ↓
Fechamento técnico
    ↓
Commit/push da branch
```
