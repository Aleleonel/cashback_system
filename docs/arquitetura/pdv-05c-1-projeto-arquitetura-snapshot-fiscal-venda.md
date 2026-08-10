# PDV-05C.1 — Projeto de Arquitetura
## Snapshot Fiscal da Venda

### 1. Objetivo

Definir a arquitetura da integração fiscal da venda no PDV, conectando o fluxo já existente de `Venda` e `ItemVenda` ao motor tributário consolidado na PDV-05B.

Esta etapa é de arquitetura e contrato.

Não implementa:

- NF-e;
- NFC-e;
- integração SEFAZ;
- certificado digital;
- contingência;
- transmissão de documento fiscal;
- autorização fiscal.

O objetivo é preparar a venda para operar com contexto fiscal consistente e histórico imutável.

---

### 2. Estado atual confirmado

A infraestrutura fiscal consolidada já possui:

```text
ConfiguracaoFiscalMatriz
ContextoSelecaoFiscal
RegraFiscal
Motor de selecao de regra
Motor tributario
Produto fiscal
Painel fiscal do produto
NCM
CEST
CFOP
CST ICMS
CSOSN
CST PIS
CST COFINS
CST IPI
Beneficio Fiscal
Origem da mercadoria
```

O PDV já possui:

```text
Venda
ItemVenda
TipoEmissaoVenda.NAO_FISCAL
TipoEmissaoVenda.FISCAL
```

Porém a venda fiscal ainda é bloqueada pelo contrato atual da finalização.

Portanto, o problema da PDV-05C não é criar o domínio fiscal novamente.

O problema é conectar:

```text
PDV
   ↓
Contexto tributario
   ↓
Resolucao fiscal do produto
   ↓
Snapshot fiscal do item
   ↓
Totais fiscais da venda
```

---

### 3. Princípio central

Uma venda finalizada deve ser historicamente imutável do ponto de vista fiscal.

Exemplo:

```text
Produto A vendido em 10/08/2026

NCM usado na venda:
2106.90.90

CFOP usado:
5102

CST ICMS usado:
00
```

Se em 20/08/2026 o cadastro do produto mudar para:

```text
NCM:
2106.90.99
```

a venda de 10/08/2026 deve continuar apresentando:

```text
2106.90.90
```

O mesmo princípio vale para:

```text
Origem da mercadoria
NCM
CEST
CFOP
CST ICMS
CSOSN
CST PIS
CST COFINS
CST IPI
Beneficio fiscal
Regra fiscal
Regime tributario
UF de origem
UF de destino
Aliquotas
Bases de calculo
Valores tributarios
```

A venda não pode reconstruir seu histórico consultando os cadastros atuais.

---

### 4. Conceito de Snapshot Fiscal

Snapshot fiscal é a fotografia dos dados tributários efetivamente usados no momento da operação.

O fluxo correto será:

```text
Produto atual
      ↓
Contexto tributario
      ↓
Regra fiscal efetiva
      ↓
Calculo tributario
      ↓
SNAPSHOT
      ↓
ItemVenda
```

Depois da finalização:

```text
ItemVenda
      ↓
Snapshot fiscal armazenado
```

e não:

```text
ItemVenda
      ↓
Produto atual
      ↓
Regra atual
```

---

### 5. Escopo do snapshot por item

Cada `ItemVenda` deverá possuir um snapshot fiscal próprio.

Proposta inicial de campos conceituais:

```text
origem_mercadoria_codigo
origem_mercadoria_descricao

ncm_codigo
ncm_descricao

cest_codigo

cfop_codigo
cfop_descricao

cst_icms_codigo
csosn_codigo

cst_pis_codigo
cst_cofins_codigo
cst_ipi_codigo

beneficio_fiscal_codigo
beneficio_fiscal_descricao

regra_fiscal_codigo
regra_fiscal_descricao

regime_tributario

uf_origem
uf_destino

tipo_operacao
finalidade_operacao
```

Dados de cálculo:

```text
base_calculo_icms
aliquota_icms
valor_icms

base_calculo_pis
aliquota_pis
valor_pis

base_calculo_cofins
aliquota_cofins
valor_cofins

base_calculo_ipi
aliquota_ipi
valor_ipi

valor_total_tributos
```

A lista final só será definida após diagnóstico específico do motor tributário existente.

---

### 6. Não usar apenas ForeignKey

O snapshot não poderá depender exclusivamente de relações como:

```python
item.regra_fiscal
item.ncm
item.cfop
```

ForeignKey pode ser útil para rastreabilidade, mas não resolve histórico.

Se a descrição, código, vigência ou regra mudar, a venda histórica poderia ficar inconsistente.

Portanto a arquitetura deverá seguir:

```text
referencia opcional ao objeto original
+
dados fiscais copiados para o snapshot
```

Exemplo conceitual:

```text
regra_fiscal_id_original
regra_fiscal_codigo_snapshot
regra_fiscal_descricao_snapshot
```

---

### 7. Snapshot do contexto da venda

Além do snapshot por item, a `Venda` deverá preservar contexto fiscal geral.

Proposta conceitual:

```text
tipo_emissao

regime_tributario_snapshot
uf_origem_snapshot
uf_destino_snapshot

configuracao_fiscal_matriz_id_original
configuracao_fiscal_versao_snapshot

consumidor_final
presenca_comprador
finalidade_operacao
tipo_operacao
```

Nem todos esses campos necessariamente serão criados agora.

O Diagnóstico 176 deverá verificar quais conceitos já existem no PDV.

---

### 8. Momento de resolução fiscal

A resolução fiscal não deve ocorrer de forma irreversível quando o produto entra no carrinho.

Motivo:

```text
cliente pode mudar
UF pode mudar
finalidade pode mudar
desconto pode mudar
quantidade pode mudar
tipo de emissao pode mudar
```

Arquitetura recomendada:

```text
ADICAO DO ITEM
    ↓
dados comerciais

RECALCULO
    ↓
simulacao fiscal

FINALIZACAO
    ↓
resolucao fiscal definitiva

COMMIT DA VENDA
    ↓
snapshot fiscal
```

---

### 9. Simulação x Snapshot definitivo

Devemos separar dois conceitos:

#### Simulação fiscal

Pode ser recalculada.

Usada durante:

```text
carrinho
alteracao de quantidade
alteracao de desconto
mudanca de cliente
mudanca de UF
```

#### Snapshot fiscal definitivo

Criado na finalização da venda.

Depois da finalização:

```text
imutavel
```

---

### 10. Contrato com resolver_produto_fiscal()

A infraestrutura atual já possui o serviço de resolução fiscal do produto.

A PDV-05C não deve replicar a lógica.

Fluxo esperado:

```text
PDV
  ↓
construir_contexto_tributario(...)
  ↓
resolver_produto_fiscal(...)
  ↓
resultado fiscal
  ↓
calcular tributos
  ↓
gerar snapshot
```

O PDV não deve selecionar `RegraFiscal` diretamente.

---

### 11. Serviço de domínio proposto

Novo serviço conceitual:

```text
pdv/services/fiscal/resolver_item_venda_fiscal.py
```

Responsabilidade:

```text
receber:
    venda
    item
    matriz
    loja
    contexto operacional

obter:
    contexto tributario
    produto fiscal efetivo
    regra fiscal
    calculo tributario

retornar:
    ResultadoFiscalItemVenda
```

Ainda não criar arquivo nesta etapa.

---

### 12. DTO proposto

Um objeto de resultado poderá representar a resolução:

```python
@dataclass(frozen=True)
class ResultadoFiscalItemVenda:
    origem_mercadoria_codigo: str
    ncm_codigo: str
    cest_codigo: str
    cfop_codigo: str

    cst_icms_codigo: str
    csosn_codigo: str
    cst_pis_codigo: str
    cst_cofins_codigo: str
    cst_ipi_codigo: str

    regime_tributario: str
    uf_origem: str
    uf_destino: str

    base_icms: Decimal
    aliquota_icms: Decimal
    valor_icms: Decimal

    base_pis: Decimal
    aliquota_pis: Decimal
    valor_pis: Decimal

    base_cofins: Decimal
    aliquota_cofins: Decimal
    valor_cofins: Decimal

    base_ipi: Decimal
    aliquota_ipi: Decimal
    valor_ipi: Decimal

    valor_total_tributos: Decimal
```

O formato exato depende do diagnóstico do `calculo_tributario.py`.

---

### 13. Persistência proposta

Existem três alternativas arquiteturais.

#### Alternativa A — campos no ItemVenda

```text
ItemVenda
    campos comerciais
    campos fiscais snapshot
```

Vantagem:

```text
consulta simples
```

Desvantagem:

```text
model muito grande
```

---

#### Alternativa B — modelo ItemVendaFiscal

```text
ItemVenda
    1:1
ItemVendaFiscal
```

Vantagens:

```text
separacao de dominio
model ItemVenda permanece comercial
evolucao fiscal independente
```

Desvantagem:

```text
join adicional
```

---

#### Alternativa C — JSON snapshot

```text
ItemVenda.snapshot_fiscal = JSONField
```

Vantagem:

```text
flexivel
```

Desvantagens:

```text
menor integridade de banco
consultas fiscais mais dificeis
menor clareza de schema
```

---

### 14. Recomendação arquitetural inicial

Preferência:

```text
ItemVendaFiscal
```

relação:

```text
ItemVenda
    1 ─── 1
ItemVendaFiscal
```

Motivos:

```text
dominio fiscal isolado
schema explícito
constraints
evolucao independente
boa auditabilidade
```

O Diagnóstico 176 deve verificar se essa solução encaixa na arquitetura atual sem duplicação.

---

### 15. Snapshot fiscal da Venda

Além do item, poderá existir:

```text
VendaFiscal
```

relação:

```text
Venda
   1 ─── 1
VendaFiscal
```

Responsabilidades:

```text
contexto fiscal geral
totais tributarios
identificacao futura do documento
status fiscal futuro
```

Porém, nesta primeira implementação talvez seja suficiente:

```text
Venda
+
ItemVendaFiscal
```

A decisão será tomada após diagnóstico.

---

### 16. Totais tributários da venda

A venda deverá consolidar:

```text
total_icms
total_pis
total_cofins
total_ipi
total_tributos
```

Regra:

```text
total fiscal da venda
=
soma dos snapshots dos itens
```

Evitar recalcular depois da finalização.

---

### 17. Relação com preço e desconto

A base fiscal deve utilizar os valores comerciais finais do item.

Fluxo:

```text
preco_unitario
quantidade
desconto
acrescimo
      ↓
valor comercial final
      ↓
base tributaria
```

Portanto o cálculo fiscal definitivo deve ocorrer depois que o valor comercial do item estiver estabilizado.

---

### 18. Atomicidade

A finalização deverá ocorrer dentro de transação.

Conceitualmente:

```python
@transaction.atomic
def finalizar_venda(...):
    validar_venda()
    recalcular_venda()
    resolver_fiscal()
    persistir_snapshots()
    registrar_pagamentos()
    registrar_movimentacao_caixa()
    finalizar()
```

Não pode ocorrer:

```text
Venda FINALIZADA
sem snapshot fiscal completo
```

quando:

```text
tipo_emissao == FISCAL
```

---

### 19. Venda não fiscal

A release atual continuará suportando:

```text
TipoEmissaoVenda.NAO_FISCAL
```

Nesse caso:

```text
snapshot fiscal obrigatório = não
```

A PDV-05C deve preservar integralmente o fluxo não fiscal já homologado.

---

### 20. Venda fiscal

Quando:

```text
tipo_emissao == FISCAL
```

o contrato futuro será:

```text
configuracao fiscal ativa
+
contexto tributario valido
+
todos os itens resolvidos
+
snapshot fiscal completo
+
totais fiscais consolidados
```

Só depois:

```text
venda pode ser finalizada
```

---

### 21. Falhas fiscais

Se um item não possuir classificação fiscal suficiente:

```text
NCM ausente
origem ausente
regra nao encontrada
regra ambigua
configuracao da matriz ausente
```

a venda fiscal não poderá finalizar.

A mensagem deverá identificar:

```text
produto
problema
acao necessaria
```

Exemplo:

```text
O produto Whey Special Flavor não possui NCM fiscal configurado.
```

---

### 22. Regra ambígua

O motor já possui conceito de regra fiscal ambígua.

Na venda:

```text
ambiguidade = erro bloqueante
```

Nunca escolher arbitrariamente uma regra para permitir venda fiscal.

---

### 23. Auditoria

O snapshot deve guardar informações suficientes para auditoria.

Possíveis campos:

```text
resolvido_em
motor_fiscal_versao
regra_fiscal_codigo
configuracao_fiscal_id_original
usuario_finalizacao
```

Não precisamos necessariamente de versionamento técnico do código agora, mas o contrato deve permitir rastreabilidade.

---

### 24. Alteração posterior de cadastros

Após finalização:

```text
alterar Produto
alterar NCM
alterar CEST
alterar RegraFiscal
alterar ConfiguracaoFiscalMatriz
```

não altera:

```text
ItemVendaFiscal
```

---

### 25. Cancelamento

Venda cancelada depois de finalizada:

```text
snapshot permanece
```

O histórico fiscal não deve ser apagado.

Uma futura operação fiscal de cancelamento será outro evento.

---

### 26. Exclusão

Snapshot fiscal não deverá aceitar exclusão isolada quando a venda estiver finalizada.

O domínio deve proteger:

```text
Venda finalizada
    ↓
ItemVendaFiscal imutavel
```

---

### 27. Preparação para documento fiscal

A PDV-05C deve produzir dados suficientes para uma futura camada:

```text
VendaFiscal
      ↓
DocumentoFiscal
      ↓
NFC-e / NF-e
```

Mas não deve implementar protocolo de autorização nesta etapa.

---

### 28. Fora do escopo PDV-05C.1

Explicitamente fora:

```text
XML NF-e
XML NFC-e
QR Code NFC-e
CSC
certificado A1/A3
assinatura XML
SEFAZ
SOAP
webservices
consulta recibo
cancelamento SEFAZ
inutilizacao
carta de correcao
contingencia
DANFE
DANFCE
```

---

### 29. Diagnóstico necessário antes da implementação

Próxima etapa:

```text
Diagnóstico 176
```

Deverá mapear:

```text
pdv/models.py
Venda
ItemVenda

pdv/services/vendas/*
finalizar_venda
recalcular_venda
validar_venda_para_finalizacao

fiscal/domain/calculo_tributario.py
fiscal/services_motor_tributario.py
produtos/services/fiscal/resolver_produto_fiscal.py
fiscal/services_contexto_tributario.py
```

Também verificar:

```text
campos atuais
constraints
migrations
testes
dependencias circulares
```

---

### 30. Perguntas que o Diagnóstico 176 deve responder

1. Onde o snapshot deve morar?

```text
ItemVenda
ou
ItemVendaFiscal
```

2. Existe local apropriado para snapshot geral?

```text
Venda
ou
VendaFiscal
```

3. Quais valores o motor tributário já retorna?

4. Quais campos ainda precisam ser calculados?

5. O `finalizar_venda()` atual permite extensão segura?

6. Existe `transaction.atomic` no fluxo?

7. Em que ponto ocorre estoque?

8. Em que ponto ocorre caixa?

9. Em que ponto a venda muda para FINALIZADA?

10. Como evitar snapshot parcialmente persistido?

---

### 31. Estratégia de implementação prevista

Se o diagnóstico confirmar a arquitetura:

```text
PDV-05C.1A
Diagnóstico do agregado Venda

PDV-05C.1B
Model do snapshot fiscal

PDV-05C.1C
Service de resolução fiscal do item

PDV-05C.1D
Integração com recalculo

PDV-05C.1E
Integração com finalização

PDV-05C.1F
Totais fiscais da venda

PDV-05C.1G
Interface / homologação
```

---

### 32. Critérios de aceite arquiteturais

A implementação futura só será aceita se:

1. venda não fiscal continuar funcionando;
2. venda fiscal usar o motor existente;
3. não houver duplicação de lógica tributária;
4. snapshot for imutável após finalização;
5. alteração do Produto não mudar venda antiga;
6. alteração da RegraFiscal não mudar venda antiga;
7. alteração da matriz não mudar venda antiga;
8. falha fiscal impedir finalização fiscal;
9. rollback for completo em falha;
10. totais fiscais forem reproduzíveis pelo snapshot.

---

### 33. Decisão arquitetural provisória

Neste projeto, a recomendação inicial é:

```text
Venda
   │
   ├── ItemVenda
   │       │
   │       └── 1:1 ItemVendaFiscal
   │
   └── totais fiscais consolidados
```

O `ItemVendaFiscal` seria o snapshot histórico.

Essa decisão ainda não autoriza criação de model.

Ela deve ser validada pelo Diagnóstico 176.

---

### 34. Resultado esperado da PDV-05C

Ao final da PDV-05C:

```text
Venda não fiscal
    continua operacional

Venda fiscal
    resolve tributação
    congela snapshot
    calcula totais
    finaliza de forma consistente
```

Ainda sem comunicação com SEFAZ.

---

### 35. Próxima etapa

```text
Diagnóstico 176
Arquitetura real do agregado Venda + integração com Motor Fiscal
```

Somente depois:

```text
Validação
Projeto final de persistência
Migration
Implementação
Testes
Homologação
```
