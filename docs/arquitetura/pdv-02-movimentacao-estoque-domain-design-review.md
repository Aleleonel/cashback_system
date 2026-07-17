# PDV-02 — Domain Design Review: MovimentacaoEstoque

## 1. Estado do documento

- Entidade: `MovimentacaoEstoque`
- Módulo: `estoque`
- Sprint: PDV-02
- Fase: desenho de domínio
- Implementação: ainda não iniciada
- Migration: ainda não criada
- Status: proposta para aprovação técnica

---

## 2. Definição

`MovimentacaoEstoque` representa um fato confirmado que alterou a posição
física de estoque de um produto em uma loja.

Exemplos:

- entrada manual;
- saída manual;
- ajuste positivo;
- ajuste negativo;
- recebimento de compra;
- venda;
- devolução;
- transferência;
- inventário;
- reversão;
- evento fiscal.

Uma movimentação não representa intenção.

Uma movimentação não representa reserva.

Uma movimentação não representa previsão.

Ela representa um efeito físico confirmado.

---

## 3. Papel no domínio

A movimentação será:

1. o histórico oficial dos fatos de estoque;
2. a origem da rastreabilidade;
3. a base para reconciliação;
4. o vínculo entre estoque e módulos externos;
5. o registro imutável de saldo anterior e posterior.

`SaldoEstoque` será a posição materializada.

`MovimentacaoEstoque` será o fato histórico.

---

## 4. Imutabilidade

Movimentações confirmadas serão imutáveis.

Não será permitido:

- alterar quantidade;
- alterar produto;
- alterar loja;
- alterar matriz;
- alterar natureza;
- alterar tipo;
- alterar origem;
- alterar documento;
- excluir a movimentação.

Correções serão realizadas por:

- reversão;
- nova movimentação compensatória;
- ajuste auditado.

Não haverá edição de movimentação pela interface.

---

## 5. Identidade

Cada movimentação possuirá UUID único.

A identidade técnica será:

- `uuid`.

A identidade de integração poderá utilizar:

- matriz;
- chave de idempotência.

A chave de idempotência não substituirá o UUID.

---

## 6. Campos propostos

### `uuid`

- `UUIDField`;
- padrão `uuid.uuid4`;
- único;
- indexado;
- não editável.

### `matriz`

- `ForeignKey` para `Matriz`;
- obrigatório;
- `PROTECT`;
- indexação composta.

### `loja`

- `ForeignKey` para `Loja`;
- obrigatório;
- `PROTECT`;
- representa a loja afetada.

### `produto`

- `ForeignKey` para `Produto`;
- obrigatório;
- `PROTECT`.

### `tipo`

- `CharField`;
- choices em `TipoMovimentacao`;
- obrigatório;
- indexado.

### `natureza`

- `CharField`;
- choices em `NaturezaMovimentacao`;
- valores:
  - entrada;
  - saída;
- obrigatório;
- indexado.

### `quantidade`

- `DecimalField`;
- `max_digits=15`;
- `decimal_places=3`;
- maior que zero;
- sempre positiva.

A natureza determina se a quantidade soma ou subtrai.

### `saldo_anterior`

- `DecimalField`;
- `max_digits=15`;
- `decimal_places=3`;
- maior ou igual a zero;
- obrigatório.

### `saldo_posterior`

- `DecimalField`;
- `max_digits=15`;
- `decimal_places=3`;
- maior ou igual a zero;
- obrigatório.

### `usuario`

- `ForeignKey` para `AUTH_USER_MODEL`;
- aceita nulo;
- `SET_NULL`;
- representa o responsável humano, quando houver.

Processos automáticos poderão não possuir usuário.

### `observacao`

- `TextField`;
- opcional;
- normalizada com `strip()`.

### `documento_referencia`

- `CharField`;
- opcional;
- tamanho proposto: 100;
- indexado;
- exemplos:
  - número de nota;
  - pedido;
  - cupom;
  - transferência;
  - inventário.

### `origem`

- `CharField`;
- choices em `OrigemMovimentacao`;
- obrigatório;
- indexado.

### `origem_id`

- `CharField`;
- opcional;
- tamanho proposto: 100;
- indexado.

Será utilizado para referência desacoplada a entidades externas.

### `chave_idempotencia`

- `CharField`;
- opcional para operações manuais;
- obrigatória para integrações;
- tamanho proposto: 150;
- indexado.

A unicidade será condicionada a valores preenchidos.

### `movimentacao_origem`

- `ForeignKey` para a própria movimentação;
- aceita nulo;
- `PROTECT`;
- usada em reversões;
- `related_name='reversoes'`.

### `grupo_transferencia`

- `UUIDField`;
- aceita nulo;
- indexado;
- une as duas movimentações da transferência.

### `criado_em`

- `DateTimeField`;
- `auto_now_add=True`;
- indexado.

---

## 7. Campos que não serão criados

Não serão armazenados:

- quantidade com sinal negativo;
- campo editável de saldo;
- status de rascunho;
- campo de exclusão lógica;
- valor monetário;
- custo médio;
- quantidade reservada;
- relação genérica Django;
- JSON de dados de origem.

A primeira versão será explícita e relacional.

---

## 8. Natureza e quantidade

Quantidade será sempre positiva.

Exemplo de entrada:

- natureza: entrada;
- quantidade: 10.000.

Exemplo de saída:

- natureza: saída;
- quantidade: 3.000.

Não será permitido:

- entrada com quantidade negativa;
- saída com quantidade negativa;
- quantidade zero.

Essa decisão evita ambiguidade e simplifica validações.

---

## 9. Tipos previstos

### Operações internas

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
- reversão_saída.

### Integrações operacionais

- compra;
- devolução_compra;
- venda;
- devolução_venda.

### Integrações fiscais

Eventos fiscais não criarão tipos físicos redundantes.

O efeito físico continuará utilizando tipos como:

- compra;
- venda;
- devolução_compra;
- devolução_venda;
- reversão_entrada;
- reversão_saída.

A procedência fiscal será representada por:

- `origem = fiscal`;
- `origem_id`;
- `documento_referencia`;
- `chave_idempotencia`.

Essa separação evita misturar tipo da operação com origem do evento.

---

## 10. Compatibilidade entre tipo e natureza

O sistema deverá validar a natureza esperada para cada tipo.

Exemplos:

- entrada_manual → entrada;
- saída_manual → saída;
- ajuste_positivo → entrada;
- ajuste_negativo → saída;
- transferência_entrada → entrada;
- transferência_saída → saída;
- inventário_entrada → entrada;
- inventário_saída → saída;
- compra → entrada;
- devolução_compra → saída;
- venda → saída;
- devolução_venda → entrada.

Essa relação será centralizada em regra de domínio.

Não será duplicada livremente em Views.

---

## 11. Saldo anterior e posterior

Para entrada:

`saldo_posterior = saldo_anterior + quantidade`

Para saída:

`saldo_posterior = saldo_anterior - quantidade`

O saldo posterior nunca poderá ser negativo na primeira versão.

A movimentação armazenará ambos os valores para:

- auditoria;
- rastreabilidade;
- investigação;
- reconciliação;
- suporte.

O banco não consegue validar sozinho toda a equação entre campos e natureza.

A regra será protegida pelo Model e principalmente pelo Service.

---

## 12. Idempotência

A idempotência impedirá aplicação duplicada da mesma operação externa.

A constraint proposta será:

- matriz;
- chave de idempotência;
- somente quando a chave estiver preenchida.

Exemplos de chave:

- `compra:123:item:5:recebimento:1`;
- `venda:987:item:2:baixa`;
- `fiscal:nfe:chave:cancelamento`;
- `transferencia:uuid:saida`;
- `transferencia:uuid:entrada`.

Quando uma chave já existir:

- nenhuma nova movimentação será criada;
- nenhum saldo será alterado novamente;
- o resultado anterior deverá ser recuperado.

O campo continuará opcional no banco para permitir registros controlados e
compatibilidade estrutural.

Entretanto, os Services de operações manuais deverão gerar ou receber uma
chave de submissão, protegendo contra clique duplo, reenvio de formulário e
repetição acidental da requisição.

---

## 13. Origem desacoplada

`origem` e `origem_id` serão usados em conjunto.

Exemplo:

- origem: compra;
- origem_id: 123.

Não será utilizada `GenericForeignKey`.

Motivos:

- menor acoplamento;
- migrations independentes;
- consultas mais previsíveis;
- integração futura com serviços externos;
- menor complexidade estrutural.

A consistência com a entidade externa será responsabilidade do Service de
integração.

---

## 14. Transferências

Transferência será uma operação composta por duas movimentações:

### Loja de origem

- tipo: transferência_saída;
- natureza: saída.

### Loja de destino

- tipo: transferência_entrada;
- natureza: entrada.

As duas compartilharão:

- `grupo_transferencia`;
- produto;
- matriz;
- documento de referência;
- origem;
- contexto transacional.

Não haverá uma única movimentação com duas lojas.

Isso mantém cada fato vinculado a uma posição específica.

---

## 15. Reversões

Uma reversão será uma nova movimentação.

Ela apontará para:

- `movimentacao_origem`.

A natureza da reversão será oposta ao fato original.

Exemplo:

Movimentação original:

- saída;
- quantidade 5.

Reversão:

- entrada;
- quantidade 5.

Regras:

- não alterar movimentação original;
- impedir reversão duplicada;
- impedir reversão parcial na primeira versão;
- impedir reversão que produza saldo impossível;
- registrar usuário, origem e motivo;
- manter idempotência.

Reversão parcial poderá ser avaliada posteriormente.

Como `movimentacao_origem` será utilizada exclusivamente pelas reversões na
primeira versão, será criada uma constraint condicional de unicidade para
impedir mais de uma reversão da mesma movimentação.

---

## 16. Ajustes

Ajuste será uma movimentação explícita.

Ajuste positivo:

- natureza: entrada.

Ajuste negativo:

- natureza: saída.

Todo ajuste exigirá:

- motivo;
- usuário;
- permissão específica;
- auditoria;
- saldo anterior;
- saldo posterior.

Ajuste não será usado como substituto silencioso para erros de integração.

---

## 17. Inventário

Cada divergência de inventário gerará uma movimentação.

Quando contagem física for maior:

- inventário_entrada.

Quando contagem física for menor:

- inventário_saída.

A origem apontará para o inventário.

O inventário será finalizado na mesma transação das movimentações.

---

## 18. Compras

Recebimento de compra produzirá entrada.

A movimentação deverá referenciar:

- compra;
- item;
- documento;
- quantidade recebida;
- chave de idempotência.

Recebimentos parciais produzirão movimentações distintas.

Cancelamento ou devolução não editarão a entrada original.

---

## 19. Vendas

Venda produzirá saída em momento definido pelo domínio da Venda.

A arquitetura deverá evitar dupla baixa entre:

- venda;
- faturamento;
- emissão fiscal.

A responsabilidade deverá estar concentrada em um único evento operacional.

Esse evento ainda será definido em Design Review próprio.

---

## 20. Devoluções

### Devolução de venda

Normalmente:

- entrada.

### Devolução de compra

Normalmente:

- saída.

A devolução será um novo fato.

Não haverá alteração da movimentação original.

---

## 21. Reserva

Reserva não será `MovimentacaoEstoque` enquanto não houver efeito físico.

Eventos como:

- criar reserva;
- liberar reserva;
- expirar reserva;

pertencerão ao futuro agregado de reserva.

Quando a reserva for consumida e houver saída física, o Service coordenará:

- consumo da reserva;
- movimentação de saída;
- atualização de saldo.

---

## 22. Fiscal

Eventos fiscais utilizarão idempotência obrigatória.

O Fiscal não criará objetos diretamente.

Ele chamará Services do Estoque.

Será necessário definir qual evento fiscal produz efeito físico.

Cancelamento fiscal produzirá:

- reversão;
- ou movimentação compensatória.

Nunca exclusão.

---

## 23. Auditoria

Cada movimentação relevante terá auditoria complementar.

A auditoria registrará:

- usuário;
- matriz;
- loja;
- produto;
- tipo;
- natureza;
- quantidade;
- saldo anterior;
- saldo posterior;
- origem;
- documento;
- chave de idempotência;
- request, quando houver.

A própria movimentação continuará sendo o registro histórico principal.

---

## 24. Invariantes

### Invariante 1

Quantidade deve ser maior que zero.

### Invariante 2

Saldo anterior e saldo posterior não podem ser negativos.

### Invariante 3

Loja deve pertencer à matriz.

### Invariante 4

Produto deve pertencer à matriz.

### Invariante 5

Produto deve controlar estoque.

### Invariante 6

Tipo e natureza devem ser compatíveis.

### Invariante 7

Saldo posterior deve corresponder à equação da operação.

### Invariante 8

Movimentação confirmada é imutável.

### Invariante 9

Movimentação não pode ser excluída.

### Invariante 10

Chave de idempotência preenchida deve ser única por matriz.

### Invariante 11

Reversão deve apontar para movimentação válida.

### Invariante 12

Uma movimentação só pode ser revertida uma vez na primeira versão.

### Invariante 13

Movimentação e saldo devem ser atualizados na mesma transação.

---

## 25. Proteções por camada

### Banco

O banco protegerá:

- quantidade maior que zero;
- saldos não negativos;
- unicidade da chave de idempotência;
- Foreign Keys;
- campos obrigatórios;
- índices;
- UUID único.

### Model

O Model protegerá:

- matriz da loja;
- matriz do produto;
- compatibilidade entre tipo e natureza;
- equação de saldo;
- normalização de strings;
- imutabilidade;
- bloqueio de exclusão.

### Service

O Service protegerá:

- autorização;
- contexto operacional;
- atomicidade;
- bloqueio do saldo;
- idempotência;
- saldo suficiente;
- criação da movimentação;
- atualização do saldo;
- reversões;
- transferências;
- auditoria.

---

## 26. Política de exclusão

A proposta será:

- Matriz: `PROTECT`;
- Loja: `PROTECT`;
- Produto: `PROTECT`;
- Usuário: `SET_NULL`;
- Movimentação de origem: `PROTECT`.

O objetivo é preservar histórico.

---

## 27. Índices propostos

- matriz, loja, criado_em;
- matriz, produto, criado_em;
- matriz, tipo, criado_em;
- matriz, natureza, criado_em;
- matriz, origem, origem_id;
- matriz, documento_referencia;
- grupo_transferencia;
- movimentacao_origem;
- chave_idempotencia.

Índices redundantes serão evitados.

---

## 28. Ordenação

Ordenação padrão:

- `-criado_em`;
- `-id`.

Isso garante histórico mais recente primeiro.

---

## 29. Interface administrativa

O Admin será somente leitura após criação.

Não será permitido:

- editar;
- excluir;
- criar movimentação manualmente sem Service.

O registro no Admin servirá para:

- consulta;
- busca;
- auditoria;
- suporte técnico.

---

## 30. Testes obrigatórios do Model

1. cria movimentação válida de entrada;
2. cria movimentação válida de saída;
3. rejeita quantidade zero;
4. rejeita quantidade negativa;
5. rejeita saldo anterior negativo;
6. rejeita saldo posterior negativo;
7. rejeita tipo e natureza incompatíveis;
8. rejeita equação incorreta;
9. rejeita loja de outra matriz;
10. rejeita produto de outra matriz;
11. rejeita produto sem controle de estoque;
12. impede chave idempotente duplicada;
13. permite chave vazia em operações permitidas;
14. preserva UUID;
15. impede edição após criação;
16. impede exclusão;
17. protege relações;
18. valida reversão;
19. impede reversão duplicada;
20. ordena histórico corretamente;
21. importa por `estoque.models`;
22. migration contém constraints e índices esperados.

---

## 31. Testes posteriores do Service

1. entrada cria saldo e movimentação;
2. saída atualiza saldo e cria movimentação;
3. saída acima do saldo falha;
4. falha executa rollback;
5. idempotência não duplica efeito;
6. concorrência não perde atualização;
7. transferência cria duas movimentações;
8. transferência é atômica;
9. ajuste exige motivo;
10. reversão cria fato oposto;
11. reversão duplicada falha;
12. inventário gera ajuste correto;
13. compra recebida gera entrada;
14. venda gera saída;
15. devolução gera natureza correta;
16. evento fiscal duplicado não reaplica estoque;
17. auditoria é registrada.

---

## 32. Questões para Design Reviews posteriores

- reversão parcial;
- transferências entre matrizes;
- estoque em trânsito;
- múltiplos depósitos;
- custo médio;
- lote;
- validade;
- número de série;
- kits;
- composição;
- conversão de unidade;
- momento exato da baixa da venda;
- integração fiscal definitiva.

---

## 33. Decisões confirmadas

- movimentação representa fato físico;
- movimentação é imutável;
- quantidade é positiva;
- natureza define entrada ou saída;
- saldo anterior e posterior são armazenados;
- tipo e natureza precisam ser compatíveis;
- idempotência é obrigatória para integrações;
- origem é desacoplada;
- transferência gera dois fatos;
- reversão gera novo fato;
- reserva sem efeito físico não é movimentação;
- Fiscal usa Services;
- movimentação não pode ser excluída;
- auditoria complementa o histórico;
- reconciliação deve ser possível.

---

## 34. Ordem de implementação do núcleo

`SaldoEstoque` e `MovimentacaoEstoque` formam o mesmo núcleo transacional.

A implementação seguirá esta ordem:

1. criar os Choices;
2. implementar `SaldoEstoque`;
3. implementar `MovimentacaoEstoque`;
4. exportar os Models;
5. registrar o app no Django;
6. manter `SaldoEstoque` na migration inicial;
7. gerar uma migration própria para `MovimentacaoEstoque`;
8. criar testes do novo Model;
9. aplicar a migration;
10. executar toda a suíte.

Os Models serão criados em migrations incrementais e revisáveis.

Não haverá Foreign Key direta de `MovimentacaoEstoque` para `SaldoEstoque`.

A associação operacional será determinada por:

- matriz;
- loja;
- produto.

O Service garantirá atualização atômica entre saldo e movimentação.

---

## 35. Critério de aprovação

O Model somente poderá ser implementado depois da aprovação de:

- campos;
- choices;
- compatibilidade tipo/natureza;
- idempotência;
- imutabilidade;
- política de reversão;
- integração com saldo;
- constraints;
- índices;
- testes.


