# PDV-05B.7.2 — Projeto 173
## Consolidação da Central de Configurações

### 1. Objetivo

Consolidar a Central de Configurações como hub administrativo principal do sistema, eliminando a sensação de telas inacabadas quando já existem funcionalidades operacionais, evitando duplicidade de módulos e preparando a sidebar definitiva.

A sprint não deve reconstruir funcionalidades que já existem.

O foco será:

- expor corretamente o que já está implementado;
- distinguir claramente função operacional, atalho, configuração e recurso futuro;
- evitar duplicidade entre Minha Empresa, Central de Configurações, módulos operacionais e sidebar;
- manter cards "Em breve" somente para funcionalidades realmente inexistentes;
- preparar a arquitetura para a futura reorganização definitiva da sidebar.

---

### 2. Premissas confirmadas pelo Diagnóstico 172

A Central de Configurações já possui:

- app próprio `configuracoes`;
- catálogo;
- componente reutilizável de cards;
- controle de acesso e decorators;
- forms;
- models;
- selectors;
- services;
- testes;
- rotas;
- views;
- templates.

Rotas e views existentes:

```text
configuracoes:inicio
configuracoes:empresa
configuracoes:usuarios_permissoes
configuracoes:criticas
configuracoes:clientes_cashback
configuracoes:vendas_comissoes
configuracoes:regras_comerciais
```

Portanto, não será criada uma nova "Central de Configurações".

---

### 3. Princípio arquitetural

A arquitetura de navegação deve seguir:

```text
SIDEBAR
  ↓
ÁREA PRINCIPAL
  ↓
HUB
  ↓
FUNÇÃO OPERACIONAL
```

Exemplos:

```text
Minha Empresa
  ↓
Configurações
  ↓
Empresa
  ↓
Lojas / Usuários / Cashback / Auditoria
```

```text
Fiscal
  ↓
Central Fiscal
  ↓
Configuração Fiscal / NCM / CEST / Regras / demais cadastros
```

A sidebar não deve tentar expor todas as funções internas de cada hub.

---

### 4. Classificação funcional inicial

#### 4.1 Central de Configurações

Estado:

```text
CONCLUÍDO E OPERACIONAL
```

Decisão:

- manter;
- usar como hub;
- não duplicar na sidebar com dezenas de atalhos;
- melhorar apenas consistência visual e status dos cards.

---

### 5. Frente 173A — Empresa

A tela `configuracoes/empresa.html` já referencia funcionalidades reais:

```text
Painel da Empresa
Lojas
Usuários
Configuração de Cashback
Auditoria
```

Essas funções possuem rotas reais no app `empresa`.

Problema atual:

- a tela ainda apresenta botões `disabled`;
- isso transmite a impressão de que as funções estão inativas mesmo quando o backend e as telas já existem.

#### Decisão

Transformar os cards correspondentes a funções já existentes em acessos operacionais.

Não criar novas views de Empresa.

Reutilizar:

```text
empresa:dashboard
empresa:lista_lojas
empresa:lista_usuarios
empresa:configurar_cashback
empresa:auditoria
```

#### Critério

Se a função existir e o usuário possuir a permissão necessária:

```text
botão ativo
```

Se existir, mas o usuário não tiver permissão:

```text
botão indisponível por permissão
```

Não usar "Em breve" para funções existentes.

---

### 6. Frente 173B — Usuários e Permissões

A tela já referencia:

```text
Lista de usuários
Criar usuário
Gestão relacionada a usuários
```

Há backend real no app `empresa`.

Problema:

- três ações aparecem visualmente desabilitadas;
- precisamos diferenciar "sem permissão" de "ainda não implementado".

#### Decisão

Separar o conceito:

```text
Gestão de usuários
→ existente

Cadastro de usuário
→ existente

Edição/status de usuário
→ existente

Gestão granular de permissões/perfis
→ revisar o que realmente existe antes de ativar
```

Não criar outro cadastro de usuários dentro de `configuracoes`.

A Central deve funcionar como hub e encaminhar para o módulo `empresa`.

---

### 7. Frente 173C — Clientes e Cashback

A tela `clientes_cashback.html` já possui atalhos reais para:

```text
Lista de Clientes
Criar Cliente
Importar Clientes
Nova Compra
```

Além disso, existe uma configuração operacional de Cashback no app `empresa`.

#### Decisão

A Central de Configurações deve separar:

```text
Clientes
→ atalhos operacionais

Cashback
→ configuração administrativa
```

A configuração oficial de Cashback continuará sendo:

```text
empresa:configurar_cashback
```

Não criar uma segunda configuração de Cashback concorrente.

---

### 8. Frente 173D — Vendas e Regras Comerciais

A área `vendas_comissoes` contém hoje:

```text
Regras Comerciais            → disponível
Tabelas de Preços            → futuro
Promoções                    → futuro
Atacado                      → futuro visual
Cashback Comercial           → futuro visual
Voucher                      → futuro visual
Brindes                      → futuro visual
Comissões                    → futuro
```

Entretanto, o model `ConfiguracaoComercial` já possui parâmetros reais para:

```text
atacado_ativo
pedido_minimo_atacado
desconto_atacado_percentual
cashback_ativo
voucher_ativo
promocoes_ativas
brindes_ativos
arredondamento_ativo
```

#### Decisão arquitetural

Não criar módulos separados imediatamente para:

```text
Atacado
Cashback Comercial
Voucher
Promoções
Brindes
```

Primeiro consolidar esses recursos dentro de:

```text
Regras Comerciais
```

porque já possuem armazenamento e formulário.

Somente criar módulo próprio no futuro se houver regra de negócio que ultrapasse simples parâmetros.

---

### 9. Regras Comerciais

Estado:

```text
CONCLUÍDO E OPERACIONAL
```

A tela já possui:

- GET;
- POST;
- form;
- model;
- service;
- validação;
- controle de edição por contexto;
- testes.

#### Decisão

Manter como fonte principal dos parâmetros comerciais.

A interface poderá ser reorganizada visualmente por grupos:

```text
Atacado
Cashback
Voucher
Promoções
Brindes
Arredondamento
```

Sem alterar o model nesta etapa.

---

### 10. Tabelas de Preços

Estado:

```text
PLACEHOLDER / AINDA NÃO IMPLEMENTADO
```

Não há evidência suficiente no Diagnóstico 172 de um módulo operacional de tabelas de preço dentro da Central.

#### Decisão

Manter como:

```text
Em breve
```

até sprint específica.

---

### 11. Comissões

Estado:

```text
PLACEHOLDER / AINDA NÃO IMPLEMENTADO
```

A própria view descreve:

```text
estrutura futura para regras, percentuais e cálculo de comissões
```

#### Decisão

Manter como:

```text
Em breve
```

Não implementar nesta sprint.

---

### 12. Promoções

Estado:

```text
PARCIAL
```

Existe apenas um parâmetro booleano:

```text
promocoes_ativas
```

Isso não equivale a uma Central de Promoções completa.

#### Decisão

Na Central de Configurações:

```text
Promoções
→ permanecer dentro de Regras Comerciais por enquanto
```

Um módulo completo de promoções poderá ser conectado ao app `campanhas` futuramente, se a arquitetura exigir.

---

### 13. Voucher

Estado:

```text
PARCIAL
```

Existe:

```text
voucher_ativo
```

e também existe app `vouchers`.

#### Decisão

Não criar outro módulo de voucher em `configuracoes`.

Usar:

```text
Regras Comerciais
→ habilita/desabilita comportamento comercial

app vouchers
→ operação e gestão do voucher
```

---

### 14. Cashback Comercial

Estado:

```text
PARCIAL / POSSÍVEL DUPLICIDADE
```

Existem hoje dois conceitos diferentes:

```text
ConfiguracaoComercial.cashback_ativo
```

e:

```text
empresa:configurar_cashback
```

#### Decisão definitiva

```text
Regras Comerciais
→ habilita/desabilita o uso comercial de Cashback

Configuração de Cashback da Empresa
→ percentuais, liberação, validade, teto, valor mínimo e comunicação
```

A UI deve explicar essa diferença.

Não duplicar campos.

---

### 15. Atacado

Estado:

```text
PARCIALMENTE IMPLEMENTADO
```

Já existem:

```text
atacado_ativo
pedido_minimo_atacado
desconto_atacado_percentual
```

e validações reais no form.

#### Decisão

Considerar Atacado como recurso existente dentro de Regras Comerciais.

Não manter um card separado como "Em breve" se ele apenas levaria aos mesmos campos.

Opções permitidas:

1. remover o card Atacado;
2. ou tornar o card Atacado um atalho para Regras Comerciais com descrição:
   "Configure pedido mínimo e desconto de atacado".

Preferência:

```text
atalho ativo para Regras Comerciais
```

---

### 16. Brindes

Estado:

```text
PARCIAL
```

Existe:

```text
brindes_ativos
```

mas não existe evidência de motor próprio de concessão/controle no Diagnóstico 172.

#### Decisão

Manter como parâmetro em Regras Comerciais.

Não criar módulo próprio nesta sprint.

---

### 17. Configurações Críticas

Estado:

```text
ESTRUTURA CRIADA
```

Existe rota, view, template e decorator específico.

Porém o Diagnóstico 172 não comprova conteúdo operacional suficiente para classificar a área como concluída.

#### Decisão

Nesta sprint:

- não inventar configurações críticas;
- revisar o template;
- manter apenas funções realmente existentes;
- se estiver vazio, apresentar mensagem clara de que não há parâmetros críticos adicionais configuráveis nesta versão.

Não apresentar cards falsos.

---

### 18. Minha Empresa

A sidebar atual já possui:

```text
Minha Empresa
  Painel da Empresa
  Configurações
```

Esse desenho é correto.

#### Decisão

Preservar essa arquitetura.

Após a consolidação:

```text
Minha Empresa
  Painel da Empresa
  Configurações
```

Dentro de Configurações:

```text
Empresa
Usuários e Permissões
Clientes e Cashback
Vendas e Regras Comerciais
Configurações Críticas
```

---

### 19. Arquivos previstos para alteração

A Aplicação 173 poderá alterar:

```text
configuracoes/catalogo.py
configuracoes/views.py
configuracoes/templates/configuracoes/empresa.html
configuracoes/templates/configuracoes/usuarios_permissoes.html
configuracoes/templates/configuracoes/clientes_cashback.html
configuracoes/templates/configuracoes/vendas_comissoes.html
configuracoes/templates/configuracoes/criticas.html
configuracoes/templates/configuracoes/regras_comerciais.html
configuracoes/templates/configuracoes/components/config_card.html
```

Possivelmente testes:

```text
configuracoes/tests/test_empresa.py
configuracoes/tests/test_usuarios_permissoes.py
configuracoes/tests/test_vendas_comissoes.py
configuracoes/tests/test_regras_comerciais_view.py
```

---

### 20. Arquivos fora de escopo

Não alterar nesta sprint:

```text
fiscal/*
pdv/*
compras/*
produtos/*
estoque/*
cashback/*
vouchers/*
campanhas/*
```

Exceto se uma validação posterior comprovar dependência indispensável.

---

### 21. Não criar nesta sprint

Não criar:

```text
novo model de comissão
novo model de tabela de preços
novo model de promoção
novo model de atacado
novo model de voucher
novo model de cashback
novo model de brindes
```

A sprint é de consolidação e navegação, não de expansão de domínio.

---

### 22. Critérios de status dos cards

Todo card deve possuir estado explícito.

#### Disponível

```text
Funcionalidade implementada e usuário autorizado.
```

#### Sem permissão

```text
Funcionalidade existe, mas o usuário atual não pode operar.
```

#### Em breve

```text
Funcionalidade realmente ainda não implementada.
```

Não utilizar `disabled` sem explicar o motivo.

---

### 23. Resultado esperado após Aplicação 173

A Central deverá transmitir:

```text
"Isso funciona"
"Isso existe, mas você não tem acesso"
"Isso ainda será desenvolvido"
```

sem ambiguidade.

O usuário não deve precisar adivinhar por que um botão está cinza.

---

### 24. Relação com a Sidebar 171

A sidebar definitiva só será aplicada após a Consolidação 173.

Motivo:

```text
primeiro definimos onde cada função mora
depois reorganizamos os acessos principais
```

Arquitetura desejada:

```text
SIDEBAR
├── Visão Geral
├── Vendas
├── PDV
├── Caixa
├── Clientes
├── Produtos e Estoque
├── Compras
├── Fiscal
│   └── Central Fiscal
├── Minha Empresa
│   ├── Painel da Empresa
│   └── Configurações
└── Administração
```

---

### 25. Testes obrigatórios da Consolidação 173

A validação deverá confirmar:

1. Central de Configurações continua acessível;
2. cards existentes continuam respeitando escopo;
3. Empresa aponta para rotas existentes;
4. Usuários aponta para rotas existentes;
5. Cashback usa configuração oficial da Empresa;
6. Regras Comerciais continua salvando;
7. Atacado não ganha backend duplicado;
8. Voucher não ganha backend duplicado;
9. Promoções não ganham backend duplicado;
10. Brindes não ganham backend duplicado;
11. Tabela de Preços permanece "Em breve";
12. Comissões permanece "Em breve";
13. botão indisponível por permissão possui explicação;
14. nenhum link gera `NoReverseMatch`;
15. `manage.py check` passa;
16. nenhum migration novo é criado.

---

### 26. Homologação visual

Validar:

#### Central

- cards organizados;
- status claros;
- nenhum botão cinza sem explicação.

#### Empresa

- Painel da Empresa abre;
- Lojas abre;
- Usuários abre;
- Cashback abre;
- Auditoria abre.

#### Usuários

- lista abre;
- criação abre quando autorizado;
- ações futuras são identificadas corretamente.

#### Vendas e Regras Comerciais

- Regras Comerciais abre;
- Atacado leva para Regras Comerciais;
- recursos apenas booleanos não parecem módulos completos;
- Tabelas de Preços aparece como futuro;
- Comissões aparece como futuro.

---

### 27. Sequência de execução

```text
Projeto 173
    ↓
Validação 173
    ↓
Aplicação 173
    ↓
Testes
    ↓
Homologação visual
    ↓
Aplicação 171 — Sidebar Definitiva
    ↓
Homologação geral de navegação
    ↓
Fechamento da PDV-05B.7
```

---

### 28. Decisão final

A Central de Configurações será mantida como **hub administrativo oficial**.

A sprint 173 não vai transformar placeholders em módulos artificiais.

Ela vai:

- ativar o que já existe;
- consolidar o que já possui backend;
- explicar restrições de permissão;
- preservar como "Em breve" somente o que realmente ainda falta;
- impedir duplicação de regras e modelos;
- preparar uma sidebar mais limpa e intuitiva.
