# PDV-02 — Blueprint consolidado do domínio de Estoque

## 1. Objetivo

Este documento define o contrato arquitetural do módulo de Estoque do Cashback System.

Ele orienta as próximas implementações sem alterar as regras já consolidadas e sem criar dependências indevidas entre Estoque, PDV, Compras, Fiscal e Auditoria.

Este blueprint deve ser consultado antes de qualquer novo Model, migration ou Service relacionado ao estoque.

---

## 2. Princípios arquiteturais

1. Models representam dados e invariantes essenciais.
2. Alterações de estado acontecem exclusivamente em Services.
3. Toda operação que altera saldo deve ser transacional.
4. Concorrência deve ser protegida com bloqueio pessimista quando necessário.
5. Movimentações de estoque são imutáveis.
6. Correções ocorrem por novas movimentações.
7. Toda operação relevante possui chave de idempotência.
8. Auditoria pertence à mesma transação da operação principal.
9. Integrações externas não atualizam saldo diretamente.
10. Abstrações compartilhadas somente serão extraídas após repetição concreta.

---

## 3. Estado atual implementado

### 3.1 SaldoEstoque

Responsável pelo saldo físico consolidado de um produto em uma loja.

Identidade lógica:

- matriz;
- loja;
- produto.

Invariantes:

- um único saldo por matriz, loja e produto;
- quantidade não negativa;
- loja e produto pertencem à mesma matriz;
- produto deve controlar estoque;
- relações protegidas contra exclusão.

### 3.2 MovimentacaoEstoque

Responsável pelo histórico imutável das alterações físicas.

Contém:

- natureza;
- tipo;
- quantidade;
- saldo anterior;
- saldo posterior;
- origem;
- documento de referência;
- chave de idempotência;
- grupo de transferência;
- movimentação original em reversões;
- usuário;
- data de criação.

### 3.3 Services implementados

Já estão implementados:

- entrada;
- saída;
- ajuste positivo;
- ajuste negativo;
- transferência entre lojas.

Todos seguem:

- transação atômica;
- bloqueio de saldo;
- validação de contexto;
- idempotência forte;
- criação de movimentação;
- atualização de saldo;
- auditoria;
- rollback completo.

---

## 4. Conceitos de saldo

O domínio distinguirá três conceitos.

### 4.1 Saldo físico

Quantidade efetivamente existente na loja.

Representado por:

```text
SaldoEstoque.quantidade_atual
```

### 4.2 Saldo reservado

Quantidade comprometida com operações ainda não concluídas.

Exemplos:

- venda aguardando confirmação;
- pedido em separação;
- retirada pendente;
- integração pendente com PDV.

### 4.3 Saldo disponível

Calculado por:

```text
saldo_disponivel = saldo_fisico - saldo_reservado
```

Regras:

- saldo disponível não pode ser negativo;
- saldo reservado não pode ser negativo;
- reserva não representa movimentação física.

---

## 5. Reserva de Estoque

A reserva não alterará imediatamente o saldo físico.

Ela possuirá entidade própria.

### 5.1 Entidade prevista

```text
ReservaEstoque
```

Campos conceituais:

- uuid;
- matriz;
- loja;
- produto;
- quantidade;
- status;
- origem;
- origem_id;
- chave_idempotencia;
- documento_referencia;
- usuario;
- expira_em;
- criada_em;
- confirmada_em;
- liberada_em;
- cancelada_em.

### 5.2 Estados previstos

```text
ATIVA
CONFIRMADA
LIBERADA
CANCELADA
EXPIRADA
```

### 5.3 Regras

- somente reserva ATIVA compromete saldo disponível;
- confirmação converte reserva em movimentação física;
- liberação devolve disponibilidade;
- cancelamento encerra a reserva;
- expiração é idempotente;
- reserva não pode exceder o saldo disponível;
- confirmação não pode ocorrer duas vezes;
- reserva encerrada não retorna para ATIVA.

### 5.4 Estratégia inicial

O saldo reservado será calculado pela soma das reservas ATIVAS.

Não será criado campo duplicado em `SaldoEstoque` inicialmente.

Motivos:

- evita inconsistência;
- mantém uma fonte única de verdade;
- reduz migrations prematuras;
- permite medir o desempenho real antes de materializar o total.

---

## 6. Inventário

Inventário representa um processo de conferência física.

Não deve ser implementado como simples ajuste direto.

### 6.1 Entidades previstas

```text
InventarioEstoque
ItemInventarioEstoque
```

### 6.2 Estados previstos

```text
ABERTO
EM_CONFERENCIA
FINALIZADO
CANCELADO
```

### 6.3 InventarioEstoque

Campos conceituais:

- uuid;
- matriz;
- loja;
- status;
- iniciado_por;
- finalizado_por;
- motivo;
- observacao;
- iniciado_em;
- finalizado_em;
- cancelado_em;
- chave_idempotencia.

### 6.4 ItemInventarioEstoque

Campos conceituais:

- inventario;
- produto;
- saldo_sistema;
- quantidade_contada;
- diferenca;
- conferido_por;
- conferido_em;
- observacao.

### 6.5 Regras

- somente um inventário aberto por loja, salvo decisão futura;
- cada produto aparece uma única vez;
- finalização é atômica;
- diferenças geram ajustes;
- inventário finalizado é imutável;
- inventário cancelado não gera ajuste;
- finalização possui idempotência;
- ajustes referenciam inventário e item.

### 6.6 Movimentações durante inventário

Na primeira versão, o inventário não bloqueará automaticamente todas as movimentações.

A diferença será recalculada no momento da finalização.

---

## 7. Devoluções

Existirão dois fluxos.

### 7.1 Devolução de venda

Efeito físico:

- entrada de estoque.

Deve referenciar:

- venda original;
- item;
- quantidade devolvida;
- motivo;
- documento fiscal quando aplicável.

### 7.2 Devolução de compra

Efeito físico:

- saída de estoque.

Deve referenciar:

- compra original;
- item;
- quantidade devolvida;
- motivo;
- documento fiscal quando aplicável.

### 7.3 Regras gerais

- quantidade devolvida não supera a quantidade elegível;
- devoluções parciais podem ser permitidas;
- total acumulado não supera a quantidade original;
- devoluções são idempotentes;
- detalhes fiscais pertencem ao módulo Fiscal.

---

## 8. Compras

Compras será responsável pelo processo comercial.

Estoque será responsável pelo efeito físico.

Fluxo:

```text
Compra recebida
    ↓
Validação comercial
    ↓
Service de entrada
    ↓
MovimentacaoEstoque do tipo COMPRA
```

Regras:

- compra em rascunho não altera estoque;
- pedido de compra não altera estoque;
- somente recebimento confirmado altera estoque;
- recebimentos parciais são permitidos;
- cada item recebido possui idempotência;
- cancelamento ocorre por reversão.

---

## 9. Vendas

Vendas ou PDV será responsável pelo processo comercial.

Estoque será responsável pelo compromisso e pelo efeito físico.

Fluxo:

```text
Venda iniciada
    ↓
Reserva
    ↓
Venda confirmada
    ↓
Confirmação da reserva
    ↓
MovimentacaoEstoque do tipo VENDA
```

Regras:

- orçamento não altera estoque físico;
- carrinho não altera estoque físico;
- venda confirmada gera saída;
- cancelamento confirmado gera reversão ou devolução;
- venda não pode baixar estoque duas vezes;
- cada item possui chave de idempotência própria.

---

## 10. Integração Fiscal

O módulo Fiscal não altera saldo diretamente.

Ele pode:

- referenciar movimentações;
- validar documentos;
- emitir notas;
- registrar cancelamentos;
- solicitar reversão por Service autorizado.

Estoque pode armazenar:

- documento_referencia;
- origem;
- origem_id.

A estrutura fiscal completa não ficará em `MovimentacaoEstoque`.

---

## 11. Reversões

Reversão é o mecanismo oficial para desfazer movimentações físicas.

Regras:

- uma movimentação possui no máximo uma reversão;
- reversão usa a mesma quantidade;
- reversão usa natureza oposta;
- não é permitido reverter uma reversão;
- operação é atômica;
- saldo é atualizado;
- auditoria é registrada;
- idempotência é obrigatória;
- movimentação original permanece imutável.

---

## 12. Auditoria

Toda operação relevante registra:

- usuário;
- matriz;
- loja;
- ação;
- recurso;
- identificador;
- descrição objetiva;
- data e hora;
- contexto de request quando disponível.

Falha da auditoria causa rollback.

---

## 13. Idempotência

Regra:

```text
mesma chave + mesmo conteúdo = reprocessamento válido
mesma chave + conteúdo diferente = conflito
```

Operações compostas geram chaves-filhas determinísticas.

Exemplo:

```text
transferencia:123:saida
transferencia:123:entrada
```

---

## 14. Concorrência

Exigem atenção concorrente:

- entrada;
- saída;
- ajuste;
- transferência;
- confirmação de reserva;
- liberação de reserva;
- finalização de inventário;
- reversão;
- recebimento de compra;
- confirmação de venda.

Diretrizes:

- usar `transaction.atomic`;
- usar `select_for_update`;
- manter ordem estável de bloqueios;
- garantir constraints críticas no banco;
- testar concorrência real em PostgreSQL.

---

## 15. Ordem de bloqueio

Operações com múltiplos saldos deverão bloquear registros em ordem determinística.

Critério recomendado:

```text
loja_id crescente
produto_id crescente
```

A transferência deverá receber testes concorrentes em PostgreSQL.

SQLite não representa adequadamente todos os comportamentos de lock.

---

## 16. Limites entre módulos

### Estoque

Responsável por:

- saldo físico;
- reservas;
- movimentações;
- transferências;
- inventários;
- reversões;
- efeitos físicos de compras e vendas.

### PDV ou Vendas

Responsável por:

- venda;
- itens;
- preços;
- descontos;
- pagamentos;
- cancelamentos comerciais;
- cliente.

### Compras

Responsável por:

- fornecedor;
- pedido;
- custo;
- recebimento comercial;
- condições de pagamento.

### Fiscal

Responsável por:

- documentos;
- impostos;
- autorizações;
- cancelamentos fiscais.

### Auditoria

Responsável por:

- trilha de ações;
- usuário;
- contexto;
- descrição;
- rastreabilidade.

---

## 17. Próximas etapas

### Etapa 1 — Reserva

Criar:

- `ReservaEstoque`;
- status;
- migration;
- criação;
- liberação;
- cancelamento;
- expiração;
- confirmação;
- selectors de reservado e disponível;
- testes.

### Etapa 2 — Reversão

Criar:

- Service de reversão;
- validação de saldo;
- idempotência;
- auditoria;
- testes.

### Etapa 3 — Inventário

Criar:

- `InventarioEstoque`;
- `ItemInventarioEstoque`;
- abertura;
- conferência;
- cancelamento;
- finalização;
- ajustes automáticos;
- testes.

### Etapa 4 — Devoluções

Criar:

- devolução de venda;
- devolução de compra;
- controle acumulado;
- testes.

### Etapa 5 — Integrações

Integrar:

- Compras;
- Vendas;
- PDV;
- Fiscal.

---

## 18. Estratégia de migrations

Sequência prevista:

```text
0001 — SaldoEstoque
0002 — MovimentacaoEstoque
0003 — ReservaEstoque
0004 — InventarioEstoque e ItemInventarioEstoque
```

Regras:

- migrations aplicadas não serão reescritas;
- novas migrations exigem Design Review;
- alterações serão incrementais;
- cada migration será validada isoladamente.

---

## 19. Extração de código compartilhado

Helpers compartilhados somente serão criados quando:

- houver pelo menos três casos reais;
- a semântica for comprovadamente igual;
- testes demonstrarem equivalência;
- a extração reduzir complexidade;
- regras específicas não sejam escondidas.

Não será criada classe-base genérica sem necessidade comprovada.

---

## 20. Critérios de conclusão do PDV-02

O módulo será funcionalmente concluído quando possuir:

- saldo físico;
- movimentações imutáveis;
- entrada;
- saída;
- ajuste;
- transferência;
- reserva;
- reversão;
- inventário;
- devoluções;
- integração com compra e venda;
- auditoria;
- idempotência;
- testes completos;
- documentação;
- validação em PostgreSQL;
- homologação operacional.

---

## 21. Decisões que exigem novo Design Review

Exigem revisão específica:

- materialização de saldo reservado;
- transferências em trânsito;
- estoque por lote;
- validade;
- número de série;
- localização interna;
- custo médio;
- FIFO;
- bloqueio durante inventário;
- estoque negativo;
- múltiplos depósitos;
- integração assíncrona;
- eventos de domínio;
- filas;
- processamento em lote;
- fechamento fiscal.

---

## 22. Decisão final

O núcleo atual está consolidado.

As próximas evoluções devem preservar:

- histórico imutável;
- saldo não negativo;
- atomicidade;
- idempotência;
- auditoria;
- isolamento por matriz;
- responsabilidade dos Services;
- migrations incrementais;
- testes antes dos commits;
- commits antes de novas etapas de risco.
