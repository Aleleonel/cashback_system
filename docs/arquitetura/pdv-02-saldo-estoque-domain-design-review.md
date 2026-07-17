# PDV-02 — Domain Design Review: SaldoEstoque

## 1. Estado do documento

- Entidade: `SaldoEstoque`
- Módulo: `estoque`
- Sprint: PDV-02
- Fase: desenho de domínio
- Implementação: ainda não iniciada
- Migration: ainda não criada
- Status: proposta para aprovação técnica

---

## 2. Definição

`SaldoEstoque` representa a posição materializada de um produto em uma loja.

Ele não representa o histórico do estoque.

Ele não representa uma movimentação.

Ele não é um campo editável pelo usuário.

Ele existe para permitir consulta eficiente da posição atual, enquanto
`MovimentacaoEstoque` preservará os fatos que produziram essa posição.

A posição será identificada pela combinação:

- matriz;
- loja;
- produto.

---

## 3. Papel no domínio

O saldo possui duas funções:

1. fornecer leitura rápida da posição atual;
2. servir como ponto de concorrência transacional durante movimentações.

O histórico oficial continuará sendo formado pelas movimentações.

O saldo materializado deverá ser reconciliável com esse histórico.

---

## 4. Fonte da verdade

Há duas perspectivas complementares:

### Fonte histórica

`MovimentacaoEstoque` será a fonte dos fatos ocorridos.

### Fonte operacional

`SaldoEstoque.quantidade_atual` será a posição materializada usada pelas
operações do dia a dia.

Em caso de divergência, a inconsistência deverá ser investigada. Não será
permitido corrigir diretamente o campo de saldo.

A correção ocorrerá por:

- ajuste auditado;
- reversão;
- inventário;
- rotina controlada de reconciliação.

---

## 5. Identidade

A identidade de negócio do saldo será:

`matriz + loja + produto`

Será criada uma constraint única para essa combinação.

Também será utilizado UUID como identificador técnico e público.

O UUID não substitui a unicidade de negócio.

---

## 6. Ciclo de vida

### Criação

O saldo será criado exclusivamente por Service do módulo Estoque.

A política inicial será criação sob demanda.

Ele poderá nascer:

- na primeira movimentação;
- durante preparação controlada de inventário;
- durante inicialização auditada de estoque;
- durante rotina explícita de criação de posições zeradas.

O cadastro de um Produto não criará automaticamente saldos para todas as
lojas.

Isso evita multiplicação desnecessária de registros.

### Estado inicial

O estado inicial será:

`quantidade_atual = 0.000`

Criar um saldo zerado não representa entrada de mercadoria.

Quando houver saldo inicial real, deverá existir uma movimentação de
`saldo_inicial`.

### Atualização

Somente Services transacionais poderão atualizar:

- quantidade atual;
- data da última movimentação.

### Exclusão

Saldos não serão excluídos durante operação normal.

Produto inativado ou descontinuado poderá continuar possuindo saldo e
histórico.

Loja inativada continuará preservando seus registros históricos.

Qualquer política futura de arquivamento deverá manter rastreabilidade.

---

## 7. Campos propostos

### `uuid`

- tipo: `UUIDField`;
- valor padrão: `uuid.uuid4`;
- não editável;
- único;
- indexado.

### `matriz`

- tipo: `ForeignKey`;
- destino: `empresas.Matriz`;
- política de exclusão proposta: `PROTECT`;
- obrigatório;
- indexação composta.

### `loja`

- tipo: `ForeignKey`;
- destino: `empresas.Loja`;
- política de exclusão proposta: `PROTECT`;
- obrigatório;
- indexação composta.

### `produto`

- tipo: `ForeignKey`;
- destino: `produtos.Produto`;
- política de exclusão proposta: `PROTECT`;
- obrigatório;
- indexação composta.

### `quantidade_atual`

- tipo: `DecimalField`;
- precisão proposta: `max_digits=15`;
- casas decimais: `decimal_places=3`;
- padrão: `Decimal('0.000')`;
- valor mínimo: zero;
- obrigatório.

Três casas decimais são compatíveis com unidades fracionáveis já previstas
no catálogo.

### `ultima_movimentacao_em`

- tipo: `DateTimeField`;
- aceita nulo;
- não será preenchido na criação de um saldo zerado sem movimentação;
- será atualizado junto da movimentação confirmada.

### `criado_em`

- tipo: `DateTimeField`;
- `auto_now_add=True`.

### `atualizado_em`

- tipo: `DateTimeField`;
- `auto_now=True`.

---

## 8. Campos que não serão criados agora

### `quantidade_reservada`

Reserva é uma capacidade obrigatória do domínio, mas deverá ser modelada com
cuidado.

Não será incluída automaticamente no primeiro Model sem a definição do fluxo
completo de:

- criação da reserva;
- expiração;
- consumo;
- liberação;
- cancelamento;
- idempotência;
- concorrência;
- vínculo com pedido ou venda.

A arquitetura deverá permitir futuramente calcular:

`quantidade_disponivel = quantidade_atual - quantidade_reservada`

Nenhuma regra da primeira versão poderá declarar que quantidade física e
quantidade disponível são conceitos permanentemente idênticos.

### `estoque_minimo`

O estoque mínimo já pertence ao Produto na primeira versão.

Não será duplicado em `SaldoEstoque` sem requisito de configuração por loja.

### custo médio

Custo médio não será armazenado no primeiro saldo operacional.

O tema será tratado na arquitetura de Compras e valorização de estoque.

---

## 9. Invariantes

### Invariante 1

Quantidade atual nunca pode ser negativa na primeira versão.

### Invariante 2

A loja deve pertencer à mesma matriz do saldo.

### Invariante 3

O produto deve pertencer à mesma matriz do saldo.

### Invariante 4

O produto deve possuir `controla_estoque=True` para participar de
movimentações.

### Invariante 5

Deve existir no máximo um saldo por matriz, loja e produto.

### Invariante 6

Nenhuma View, Form, comando externo ou módulo integrado pode atualizar saldo
diretamente.

### Invariante 7

Toda alteração quantitativa deve possuir movimentação correspondente.

### Invariante 8

A quantidade será armazenada com três casas decimais e normalizada pelo
Service.

### Invariante 9

O saldo deverá ser bloqueado durante operações concorrentes.

### Invariante 10

Saldo zerado é um estado válido.

---

## 10. Proteções por camada

### Banco de dados

O banco protegerá:

- unicidade de matriz, loja e produto;
- quantidade maior ou igual a zero;
- campos obrigatórios;
- integridade das Foreign Keys;
- índices.

### Model

O Model protegerá:

- compatibilidade entre matriz e loja;
- compatibilidade entre matriz e produto;
- quantidade não negativa;
- normalização estrutural;
- validação antes de persistência quando aplicável.

O Model não decidirá tipos de movimentação.

O Model não calculará entradas e saídas.

### Service

O Service protegerá:

- autorização operacional;
- contexto de matriz e loja;
- produto controlado;
- bloqueio concorrente;
- saldo suficiente;
- criação da movimentação;
- atualização do saldo;
- idempotência;
- auditoria;
- atomicidade;
- integrações futuras.

### View

A View apenas coordenará:

- autenticação;
- permissão;
- Form;
- chamada do Service;
- mensagens;
- resposta.

---

## 11. Concorrência

Toda alteração de saldo ocorrerá em `transaction.atomic()`.

O registro de saldo será obtido com `select_for_update()`.

Quando o saldo ainda não existir, o Service deverá tratar com cuidado a
criação concorrente.

Estratégia prevista:

1. procurar ou criar a posição dentro da transação;
2. utilizar constraint única;
3. tratar eventual `IntegrityError`;
4. recuperar a posição criada pela transação concorrente;
5. bloquear o registro;
6. continuar a operação.

A implementação deverá evitar:

- lost update;
- saldo calculado sobre valor desatualizado;
- duas posições para o mesmo produto e loja;
- aplicação duplicada de uma movimentação.

---

## 12. Ordem de bloqueio

Operações simples bloquearão um saldo.

Transferências bloquearão dois saldos.

Para prevenir deadlock, transferências deverão bloquear os registros em ordem
determinística, por exemplo:

1. menor `loja_id`;
2. maior `loja_id`;
3. produto.

A regra exata será definida no Design Review de Transferência.

---

## 13. Integração com transferências

Uma transferência produzirá:

- saída na loja de origem;
- entrada na loja de destino;
- duas movimentações;
- um mesmo grupo de transferência;
- atualização de dois saldos;
- uma única transação.

Não haverá alteração parcial.

---

## 14. Integração com inventário

A abertura do inventário registrará a posição do sistema.

A finalização comparará:

- quantidade registrada pelo sistema;
- quantidade física contada.

A diferença produzirá movimentação:

- positiva, quando contado for maior;
- negativa, quando contado for menor.

O inventário não escreverá diretamente em `SaldoEstoque`.

Ele chamará o Service de movimentação.

---

## 15. Integração com ajustes

Ajustes serão operações explícitas e auditadas.

Não serão equivalentes a editar saldo.

Cada ajuste exigirá:

- tipo;
- quantidade positiva;
- motivo;
- usuário;
- loja;
- produto;
- movimentação;
- auditoria.

---

## 16. Integração com compras

O módulo de Compras não atualizará saldo diretamente.

O recebimento confirmado chamará o Service de entrada.

A integração deverá fornecer:

- compra;
- item da compra;
- documento;
- quantidade recebida;
- chave de idempotência;
- loja;
- produto.

Recebimento parcial deverá produzir movimentos parciais identificáveis.

---

## 17. Integração com vendas

O módulo de Venda ou PDV não atualizará saldo diretamente.

A confirmação operacional chamará o Service de saída.

A etapa exata de baixa deverá ser definida no domínio de Venda:

- confirmação;
- faturamento;
- emissão fiscal;
- conclusão.

A arquitetura deverá evitar baixa duplicada entre Venda e Fiscal.

---

## 18. Integração com devoluções

### Devolução de venda

Normalmente produzirá entrada.

### Devolução de compra

Normalmente produzirá saída.

A devolução terá:

- origem própria;
- referência ao documento;
- chave de idempotência;
- movimentação própria;
- auditoria.

Não será feita alteração na movimentação original.

---

## 19. Integração com reserva

Reserva não altera necessariamente o saldo físico.

Ela reduz a disponibilidade operacional.

O domínio deverá distinguir:

- quantidade física;
- quantidade reservada;
- quantidade disponível.

Uma reserva futura deverá possuir ciclo de vida próprio:

- ativa;
- parcialmente consumida;
- consumida;
- liberada;
- expirada;
- cancelada.

O consumo da reserva e a saída física deverão ocorrer de forma coordenada.

---

## 20. Integração fiscal

O módulo Fiscal registrará eventos, mas utilizará Services do Estoque.

Será necessário definir claramente qual evento produz efeito físico.

Exemplos futuros:

- emissão autorizada;
- cancelamento autorizado;
- devolução fiscal;
- entrada por documento fiscal;
- saída por documento fiscal.

A idempotência será obrigatória para evitar processamento duplicado de
retornos fiscais.

---

## 21. Auditoria

A auditoria deverá registrar:

- usuário;
- matriz;
- loja;
- recurso;
- saldo afetado;
- movimentação;
- operação;
- quantidade;
- saldo anterior;
- saldo posterior;
- documento de referência;
- origem;
- data e hora;
- IP e user-agent quando houver request.

A auditoria não substituirá `MovimentacaoEstoque`.

---

## 22. Reconciliação

Deverá ser possível calcular:

`saldo_recalculado = entradas - saídas`

E comparar com:

`SaldoEstoque.quantidade_atual`

Uma rotina futura de reconciliação deverá:

1. localizar divergências;
2. não corrigir silenciosamente;
3. gerar relatório;
4. exigir operação controlada para correção;
5. preservar auditoria.

---

## 23. Índices propostos

### Constraint e índice principal

- matriz;
- loja;
- produto.

### Consultas por produto

- matriz;
- produto.

### Consultas operacionais da loja

- matriz;
- loja;
- quantidade atual.

### Movimentação recente

- loja;
- última movimentação.

Os nomes deverão respeitar os limites do banco e o padrão do projeto.

Índices redundantes não serão criados sem necessidade.

---

## 24. Política de exclusão das relações

A proposta inicial é utilizar `PROTECT` para:

- matriz;
- loja;
- produto.

A finalidade é impedir perda de integridade histórica.

Essa decisão será confirmada ao revisar os Models atuais de Matriz, Loja e
Produto antes da implementação.

---

## 25. Interface administrativa

O Admin não permitirá alteração manual de quantidade.

Quando o Model for registrado no Admin:

- quantidade será somente leitura;
- relações serão somente leitura após criação;
- exclusão será bloqueada;
- ações de movimentação não serão implementadas diretamente no Admin.

Operações deverão utilizar a interface e os Services próprios.

---

## 26. Testes obrigatórios do Model

1. cria saldo zerado válido;
2. rejeita quantidade negativa;
3. impede duplicidade de matriz, loja e produto;
4. rejeita loja de outra matriz;
5. rejeita produto de outra matriz;
6. aceita saldo zero;
7. aceita quantidade com três casas decimais;
8. preserva UUID;
9. protege relações;
10. atualiza timestamps;
11. importa o Model por `estoque.models`;
12. migration é estável;
13. constraint existe no banco;
14. índices esperados existem na migration;
15. não permite estado estrutural impossível.

---

## 27. Testes posteriores do Service

1. cria saldo na primeira entrada;
2. reutiliza saldo existente;
3. bloqueia saldo concorrente;
4. impede saída superior ao saldo;
5. aplica entrada corretamente;
6. aplica saída corretamente;
7. cria movimentação correspondente;
8. registra auditoria;
9. executa rollback completo em falha;
10. não duplica operação idempotente;
11. respeita matriz;
12. respeita loja;
13. respeita produto controlado;
14. realiza transferência atômica;
15. suporta futura reserva sem acoplamento direto.

---

## 28. Decisões confirmadas

- saldo é materializado;
- movimentação é histórica;
- saldo não é digitado;
- saldo zero é válido;
- saldo negativo é proibido inicialmente;
- saldo pertence a matriz, loja e produto;
- criação será sob demanda;
- operações utilizarão Decimal com três casas;
- Services serão a única porta de escrita;
- não serão usados signals;
- concorrência será protegida;
- transferências serão atômicas;
- inventário gera ajustes;
- compras e vendas integram por Service;
- devoluções geram novos fatos;
- reserva será conceito separado;
- Fiscal não escreverá diretamente;
- auditoria será obrigatória;
- reconciliação deverá ser possível.

---

## 29. Questões que pertencem a Designs Reviews posteriores

Estas questões não bloqueiam o primeiro Model de saldo:

- estrutura definitiva de ReservaEstoque;
- momento exato da baixa de uma Venda;
- custo médio;
- lotes e validade;
- serialização;
- regras fiscais específicas;
- transferências entre matrizes;
- estoque em trânsito;
- múltiplos depósitos na mesma loja;
- localização física;
- unidade de conversão;
- kits e composição de produtos.

Elas deverão ser avaliadas cuidadosamente antes da implementação das
respectivas capacidades.

---

## 30. Critério de aprovação

O Model `SaldoEstoque` somente poderá ser implementado depois que:

- este documento for revisado;
- os campos forem aprovados;
- as invariantes forem aprovadas;
- a política de criação for aprovada;
- a precisão da quantidade for aprovada;
- a política de exclusão for confirmada;
- o plano de testes for aprovado.

---

## 31. Estratégia de migrations

A implementação do núcleo será incremental.

A migration inicial do app conterá:

- `SaldoEstoque`.

A migration seguinte conterá:

- `MovimentacaoEstoque`.

Essa decisão permite revisar e testar cada entidade isoladamente, sem alterar
o relacionamento transacional definido no domínio.

A atomicidade entre saldo e movimentação continuará sendo responsabilidade
dos Services, independentemente de os Models terem sido criados em migrations
separadas.
