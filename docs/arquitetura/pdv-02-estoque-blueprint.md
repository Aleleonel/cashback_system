# PDV-02 — Blueprint Arquitetural do Módulo Estoque

## 1. Objetivo

Implementar o controle de estoque por loja com histórico completo,
isolamento por matriz, operações transacionais, auditoria e integração
segura com os futuros módulos de Compras e Frente de Caixa.

O estoque não será armazenado diretamente no cadastro do Produto.

O campo `Produto.controla_estoque` continuará indicando se o item participa
ou não do controle de estoque.

O campo `Produto.estoque_minimo` será utilizado inicialmente como referência
de estoque mínimo. Um estoque mínimo específico por loja somente será criado
se houver requisito real para isso.

---

## 2. Princípios obrigatórios

1. Nenhum módulo externo altera saldo diretamente.
2. Toda alteração de saldo passa por um Service do módulo Estoque.
3. Toda operação de saldo ocorre dentro de `transaction.atomic()`.
4. O saldo é bloqueado com `select_for_update()` durante a movimentação.
5. Movimentações confirmadas são imutáveis.
6. Correções são feitas por movimentações de reversão ou ajuste.
7. Quantidades de movimentação são sempre positivas.
8. O sentido da operação é definido pela natureza: entrada ou saída.
9. O saldo não pode ficar negativo na primeira versão.
10. Toda consulta operacional respeita matriz e loja.
11. Toda operação relevante registra auditoria.
12. Integrações futuras devem utilizar chave de idempotência.
13. Não haverá signals para movimentar estoque.
14. Models protegem integridade estrutural.
15. Services concentram regras transacionais.
16. Selectors concentram consultas.
17. Views apenas coordenam entrada, Service e resposta.

---

## 3. Limites da Sprint PDV-02

### Incluído

- saldo atual por produto e loja;
- entradas manuais;
- saídas manuais;
- ajustes positivos e negativos;
- transferências entre lojas;
- histórico de movimentações;
- inventário físico;
- alertas de estoque mínimo;
- permissões;
- auditoria;
- Services e Selectors;
- Forms e Views operacionais;
- testes completos.

### Não incluído nesta sprint

- compras e fornecedores;
- pedidos de venda;
- emissão fiscal;
- lotes e validade;
- números de série;
- reserva de estoque;
- custo médio contábil;
- integração com balanças;
- importação de saldo inicial por planilha;
- estoque mínimo diferente por loja.

Esses itens somente serão adicionados por requisito específico.

---

## 4. Entidades

### 4.1. SaldoEstoque

Representa o estado atual do produto em uma loja.

Campos previstos:

- `uuid`;
- `matriz`;
- `loja`;
- `produto`;
- `quantidade_atual`;
- `ultima_movimentacao_em`;
- `criado_em`;
- `atualizado_em`.

Regras:

- combinação única de matriz, loja e produto;
- matriz da loja deve ser a mesma matriz do saldo;
- matriz do produto deve ser a mesma matriz do saldo;
- quantidade atual nunca pode ser negativa;
- produto com `controla_estoque=False` não possui movimentação;
- saldo é criado pelo Service quando necessário;
- nenhuma View altera esse Model diretamente.

Índices previstos:

- matriz, loja e produto;
- matriz e produto;
- loja e quantidade atual;
- loja e ultima movimentação.

Não será criado campo de quantidade reservada nesta sprint.

---

### 4.2. MovimentacaoEstoque

Representa todo evento confirmado que alterou um saldo.

Campos previstos:

- `uuid`;
- `matriz`;
- `loja`;
- `produto`;
- `tipo`;
- `natureza`;
- `quantidade`;
- `saldo_anterior`;
- `saldo_posterior`;
- `usuario`;
- `observacao`;
- `documento_referencia`;
- `origem`;
- `origem_id`;
- `chave_idempotencia`;
- `movimentacao_origem`;
- `grupo_transferencia`;
- `criado_em`.

Regras:

- quantidade deve ser maior que zero;
- natureza será entrada ou saída;
- saldo posterior deve corresponder à operação;
- movimentação confirmada não pode ser editada;
- movimentação confirmada não pode ser excluída;
- reversão aponta para a movimentação original;
- uma movimentação só pode ser revertida uma vez;
- chave de idempotência impede duplicidade;
- origem e origem_id permitem integração futura sem ForeignKey direta;
- grupo de transferência une a saída e a entrada da mesma transferência.

A movimentação será o histórico oficial do estoque.

---

### 4.3. InventarioEstoque

Representa uma conferência física de uma loja.

Campos previstos:

- `uuid`;
- `matriz`;
- `loja`;
- `codigo`;
- `descricao`;
- `status`;
- `aberto_por`;
- `aberto_em`;
- `finalizado_por`;
- `finalizado_em`;
- `cancelado_por`;
- `cancelado_em`;
- `observacao`;
- `criado_em`;
- `atualizado_em`.

Estados previstos:

- rascunho;
- aberto;
- em_conferencia;
- finalizado;
- cancelado.

Regras:

- apenas inventários não finalizados podem ser alterados;
- inventário finalizado é imutável;
- inventário cancelado não gera movimentações;
- finalização ocorre em transação única;
- cada divergência gera movimentação de ajuste;
- não será permitido finalizar inventário sem itens;
- não será permitido finalizar duas vezes.

---

### 4.4. InventarioItem

Representa a contagem de um produto no inventário.

Campos previstos:

- `uuid`;
- `inventario`;
- `produto`;
- `quantidade_sistema`;
- `quantidade_contada`;
- `diferenca`;
- `observacao`;
- `conferido_por`;
- `conferido_em`;
- `criado_em`;
- `atualizado_em`.

Regras:

- produto único por inventário;
- quantidade contada não pode ser negativa;
- quantidade do sistema é registrada como fotografia da abertura;
- diferença é calculada por:
  `quantidade_contada - quantidade_sistema`;
- item de inventário finalizado não pode ser alterado;
- produto deve pertencer à mesma matriz do inventário;
- produto deve controlar estoque.

---

## 5. Choices previstos

### NaturezaMovimentacao

- entrada;
- saída.

### TipoMovimentacao

- saldo_inicial;
- entrada_manual;
- saída_manual;
- ajuste_positivo;
- ajuste_negativo;
- transferência_entrada;
- transferência_saída;
- inventário_entrada;
- inventário_saída;
- reversão_entrada;
- reversão_saída;
- compra;
- venda;
- cancelamento_compra;
- cancelamento_venda.

Os tipos de Compra e Venda serão reservados para integrações futuras.

### OrigemMovimentacao

- manual;
- inventário;
- transferência;
- compra;
- venda;
- sistema.

### StatusInventario

- rascunho;
- aberto;
- em_conferencia;
- finalizado;
- cancelado.

---

## 6. Fluxo transacional de movimentação

Toda movimentação seguirá a sequência:

1. validar usuário e contexto operacional;
2. validar matriz, loja e produto;
3. validar `Produto.controla_estoque`;
4. validar chave de idempotência;
5. iniciar `transaction.atomic()`;
6. obter ou criar saldo;
7. bloquear saldo com `select_for_update()`;
8. calcular saldo posterior;
9. impedir saldo negativo;
10. criar movimentação imutável;
11. atualizar saldo atual;
12. registrar auditoria;
13. confirmar a transação;
14. retornar saldo e movimentação.

Nenhuma etapa intermediária será confirmada isoladamente.

---

## 7. Fluxo de transferência

Uma transferência entre lojas será uma operação única.

Dentro da mesma transação:

1. validar que as lojas pertencem à mesma matriz;
2. impedir transferência para a mesma loja;
3. bloquear os dois saldos em ordem determinística;
4. gerar saída na loja de origem;
5. gerar entrada na loja de destino;
6. utilizar o mesmo `grupo_transferencia`;
7. registrar auditoria da transferência;
8. confirmar ou desfazer tudo.

Não existirá transferência parcialmente concluída.

---

## 8. Fluxo de inventário

### Abertura

1. criar inventário;
2. selecionar produtos que controlam estoque;
3. registrar quantidade atual em cada item;
4. alterar status para aberto;
5. registrar auditoria.

### Conferência

1. registrar quantidade contada;
2. identificar usuário e horário da conferência;
3. calcular diferença;
4. manter inventário editável até a finalização.

### Finalização

1. bloquear o inventário;
2. bloquear os saldos afetados;
3. recalcular e validar o estado;
4. gerar ajustes positivos ou negativos;
5. marcar inventário como finalizado;
6. registrar usuário e horário;
7. registrar auditoria;
8. confirmar tudo na mesma transação.

---

## 9. Política de saldo negativo

Na primeira versão, saldo negativo será proibido.

Serão bloqueadas:

- saídas manuais acima do saldo;
- ajustes negativos acima do saldo;
- transferências acima do saldo;
- reversões que produzam saldo negativo;
- finalizações de inventário inconsistentes.

Uma futura configuração de saldo negativo somente será adicionada mediante
requisito explícito.

---

## 10. Idempotência

Services que possam ser chamados por integrações receberão
`chave_idempotencia`.

Quando a mesma chave for enviada novamente:

- nenhuma nova movimentação será criada;
- o resultado original será devolvido;
- a quantidade não será aplicada duas vezes.

A unicidade deverá respeitar o contexto da matriz.

---

## 11. Imutabilidade

Movimentações não terão fluxo de edição.

Não será permitido:

- alterar quantidade;
- alterar produto;
- alterar loja;
- alterar natureza;
- excluir movimentação confirmada.

Correções serão feitas por:

- reversão da movimentação original;
- nova movimentação de ajuste.

A proteção será aplicada no Service, no Model e na interface administrativa.

---

## 12. Permissões previstas

- `estoque.visualizar`;
- `estoque.movimentar`;
- `estoque.ajustar`;
- `estoque.transferir`;
- `estoque.inventarios_visualizar`;
- `estoque.inventarios_gerenciar`.

Distribuição inicial proposta:

### Master

Todas as permissões.

### Admin da loja

Todas as permissões operacionais de estoque.

### Operador

- visualizar estoque;
- movimentar, somente se definido pelo perfil;
- sem ajuste por padrão;
- sem transferência por padrão;
- sem finalização de inventário por padrão.

Permissões administrativas poderão entrar na lista de permissões extras.

---

## 13. Auditoria prevista

Recursos:

- `estoque.movimentacao`;
- `estoque.transferencia`;
- `estoque.inventario`;
- `estoque.inventario_item`;
- `estoque.acesso_negado`.

Eventos:

- criar movimentação;
- realizar ajuste;
- transferir estoque;
- abrir inventário;
- registrar conferência;
- finalizar inventário;
- cancelar inventário;
- reverter movimentação;
- tentativa de acesso negado.

A auditoria complementa o histórico, mas não substitui
`MovimentacaoEstoque`.

---

## 14. Selectors previstos

### Saldos

- listar saldos por matriz e loja;
- buscar saldo de produto;
- listar estoque abaixo do mínimo;
- listar produtos sem saldo;
- buscar posição consolidada por produto.

### Movimentações

- listar histórico;
- filtrar por loja;
- filtrar por produto;
- filtrar por tipo;
- filtrar por natureza;
- filtrar por período;
- localizar por UUID;
- localizar por chave de idempotência.

### Inventários

- listar inventários;
- buscar inventário;
- listar itens;
- listar divergências;
- verificar inventário aberto por loja.

Selectors nunca alterarão dados.

---

## 15. Services previstos

### Movimentações

- registrar entrada;
- registrar saída;
- registrar ajuste positivo;
- registrar ajuste negativo;
- realizar transferência;
- reverter movimentação.

### Inventários

- criar inventário;
- abrir inventário;
- registrar contagem;
- finalizar inventário;
- cancelar inventário.

Services serão a única porta de escrita do módulo.

---

## 16. Forms previstos

- filtro de saldos;
- entrada manual;
- saída manual;
- ajuste de estoque;
- transferência;
- criação de inventário;
- conferência de item;
- finalização de inventário.

Forms serão responsáveis por apresentação e validação imediata.

Regras críticas continuarão protegidas nos Services.

---

## 17. Views previstas

- posição de estoque;
- histórico de movimentações;
- detalhe da movimentação;
- entrada manual;
- saída manual;
- ajuste;
- transferência;
- lista de inventários;
- criação de inventário;
- detalhe do inventário;
- conferência;
- finalização;
- cancelamento.

Views utilizarão permissões, contexto operacional, Forms, Selectors e
Services.

---

## 18. Estratégia de testes

### Models

- constraints;
- validação de matriz;
- quantidade não negativa;
- unicidade;
- imutabilidade;
- cálculo de diferença.

### Services

- entrada;
- saída;
- saldo insuficiente;
- ajuste;
- transferência atômica;
- reversão;
- idempotência;
- concorrência;
- rollback;
- inventário;
- auditoria.

### Selectors

- isolamento por matriz;
- isolamento por loja;
- filtros;
- estoque mínimo;
- histórico;
- divergências.

### Permissões

- master;
- admin da loja;
- operador;
- permissões extras;
- acessos negados.

### Views

- autenticação;
- permissão;
- matriz e loja;
- mensagens;
- redirecionamentos;
- POST inválido;
- POST válido;
- paginação.

Após cada etapa:

1. `python manage.py check`;
2. testes do módulo alterado;
3. testes completos do projeto;
4. revisão do Git diff;
5. commit pequeno e descritivo.

---

## 19. Sequência de implementação

1. registrar o app no Django;
2. criar Choices;
3. criar `SaldoEstoque`;
4. testar `SaldoEstoque`;
5. criar `MovimentacaoEstoque`;
6. testar imutabilidade e constraints;
7. criar Service central de movimentação;
8. testar transações e concorrência;
9. criar entradas, saídas e ajustes;
10. criar transferências;
11. criar reversões;
12. criar Selectors de saldo e movimentação;
13. criar permissões;
14. criar inventário e itens;
15. criar Services de inventário;
16. criar Forms;
17. criar Views;
18. criar templates;
19. integrar menu;
20. executar homologação completa.

Nenhuma etapa deve antecipar código da etapa seguinte sem necessidade.

---

## 20. Critérios de conclusão da PDV-02

A sprint somente será considerada concluída quando:

- migrations estiverem aplicadas;
- `python manage.py check` estiver aprovado;
- testes do Estoque estiverem aprovados;
- todos os testes do projeto estiverem aprovados;
- permissões estiverem validadas;
- auditoria estiver validada;
- nenhuma escrita direta em saldo existir fora dos Services;
- movimentações forem imutáveis;
- saldo negativo estiver bloqueado;
- transferências forem atômicas;
- inventários forem atômicos;
- documentação estiver atualizada;
- branch estiver limpa;
- homologação manual estiver concluída.
