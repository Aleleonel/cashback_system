# PDV-05C.1B — Projeto 179B
## Contrato Final do Serviço de Snapshot Fiscal

### 1. Objetivo

Definir o contrato definitivo do serviço responsável por transformar:

- `Venda`;
- `ItemVenda`;
- contexto tributário;
- produto fiscal resolvido;
- resultado do motor tributário;

em dados persistíveis de:

- `VendaFiscal`;
- `ItemVendaFiscal`.

Esta etapa ainda não integra o serviço ao `finalizar_venda()`.

---

## 2. Arquivo proposto

```text
pdv/services/fiscal/snapshot_venda.py
```

Pacote:

```text
pdv/services/fiscal/
    __init__.py
    snapshot_venda.py
```

O módulo poderá importar:

```text
fiscal
produtos
pdv.models
```

Mas:

```text
fiscal
produtos
```

não deverão importar `pdv` para executar o snapshot.

---

## 3. Princípio central

O snapshot deve armazenar o que foi efetivamente usado no cálculo.

Não deve reconstruir posteriormente:

- regra;
- alíquota;
- redução;
- diferimento;
- base;
- classificação fiscal;

consultando cadastros atuais.

---

## 4. Camadas do serviço

O serviço será dividido em quatro responsabilidades:

```text
1. construir dados fiscais do item
2. persistir snapshot do item
3. consolidar dados fiscais da venda
4. persistir snapshot da venda
```

---

## 5. DTO — DadosItemVendaFiscal

Proposta:

```python
@dataclass(frozen=True, slots=True)
class DadosItemVendaFiscal:
    regra_fiscal_id_original: int | None
    configuracao_fiscal_id_original: int | None

    origem_mercadoria_codigo: str
    ncm_codigo: str
    ncm_descricao: str
    cest_codigo: str
    cfop_codigo: str
    cfop_descricao: str

    cst_icms_codigo: str
    csosn_codigo: str
    cst_pis_codigo: str
    cst_cofins_codigo: str
    cst_ipi_codigo: str

    beneficio_fiscal_codigo: str
    beneficio_fiscal_descricao: str
    regra_fiscal_codigo: str
    regra_fiscal_descricao: str

    regime_tributario: str
    uf_origem: str
    uf_destino: str
    tipo_operacao: str
    finalidade_operacao: str
    contribuinte_icms: bool
    consumidor_final: bool

    quantidade: Decimal
    valor_unitario: Decimal
    valor_produtos: Decimal
    desconto: Decimal
    acrescimo: Decimal
    frete: Decimal
    seguro: Decimal
    outras_despesas: Decimal
    base_operacao: Decimal

    base_icms: Decimal
    aliquota_icms: Decimal | None
    percentual_reducao_base_icms: Decimal
    valor_icms_bruto: Decimal
    percentual_diferimento_icms: Decimal
    valor_icms_diferido: Decimal
    valor_icms: Decimal

    base_fcp: Decimal
    aliquota_fcp: Decimal | None
    valor_fcp: Decimal

    base_pis: Decimal
    aliquota_pis: Decimal | None
    valor_pis: Decimal

    base_cofins: Decimal
    aliquota_cofins: Decimal | None
    valor_cofins: Decimal

    base_ipi: Decimal
    aliquota_ipi: Decimal | None
    valor_ipi: Decimal

    valor_total_tributos: Decimal
```

---

## 6. DTO — DadosVendaFiscal

```python
@dataclass(frozen=True, slots=True)
class DadosVendaFiscal:
    configuracao_fiscal_id_original: int | None

    regime_tributario: str
    uf_origem: str
    uf_destino: str
    tipo_operacao: str
    finalidade_operacao: str
    contribuinte_icms: bool
    consumidor_final: bool

    total_base_operacao: Decimal
    total_base_icms: Decimal
    total_icms: Decimal
    total_fcp: Decimal
    total_base_pis: Decimal
    total_pis: Decimal
    total_base_cofins: Decimal
    total_cofins: Decimal
    total_base_ipi: Decimal
    total_ipi: Decimal
    total_tributos: Decimal
```

---

# 7. Matriz Campo → Origem — Contexto

| Campo snapshot | Fonte |
|---|---|
| `regime_tributario` | `contexto_tributario.regime_tributario` |
| `uf_origem` | `contexto_tributario.uf_origem` |
| `uf_destino` | `contexto_tributario.uf_destino` |
| `tipo_operacao` | `contexto_tributario.tipo_operacao` |
| `finalidade_operacao` | `contexto_tributario.finalidade_operacao` |
| `contribuinte_icms` | `contexto_tributario.contribuinte_icms` |
| `consumidor_final` | `contexto_tributario.consumidor_final` |
| `configuracao_fiscal_id_original` | configuração usada para construir o contexto |

Regra:

```text
não buscar novamente ConfiguracaoFiscalMatriz durante persistência
```

O ID deve ser carregado junto com a preparação do contexto fiscal.

---

# 8. Matriz Campo → Origem — Comercial

| Campo snapshot | Fonte |
|---|---|
| `quantidade` | `item_venda.quantidade` |
| `valor_unitario` | `item_venda.preco_unitario` |
| `valor_produtos` | `item_venda.subtotal` |
| `desconto` | `item_venda.desconto` |
| `acrescimo` | `item_venda.acrescimo` |
| `frete` | contexto de cálculo |
| `seguro` | contexto de cálculo |
| `outras_despesas` | contexto de cálculo |

Nesta primeira integração:

```text
frete = 0
seguro = 0
outras_despesas = 0
```

somente se o contexto de cálculo atual já for construído explicitamente com esses valores.

Não inventar fallback silencioso dentro do snapshot.

---

# 9. Matriz Campo → Origem — Resultado do motor

Copiar diretamente de `ResultadoCalculoTributario`:

| Snapshot | Resultado |
|---|---|
| `base_operacao` | `resultado.base_operacao` |
| `base_icms` | `resultado.base_icms` |
| `valor_icms_bruto` | `resultado.valor_icms_bruto` |
| `valor_icms_diferido` | `resultado.valor_icms_diferido` |
| `valor_icms` | `resultado.valor_icms` |
| `base_fcp` | `resultado.base_fcp` |
| `valor_fcp` | `resultado.valor_fcp` |
| `base_pis` | `resultado.base_pis` |
| `valor_pis` | `resultado.valor_pis` |
| `base_cofins` | `resultado.base_cofins` |
| `valor_cofins` | `resultado.valor_cofins` |
| `base_ipi` | `resultado.base_ipi` |
| `valor_ipi` | `resultado.valor_ipi` |
| `valor_total_tributos` | `resultado.valor_total_tributos` |

Não recalcular esses campos no PDV.

---

# 10. Matriz Campo → Origem — Alíquotas

Fonte preferencial:

```python
resultado.memoria_calculo["tributos"]
```

Mapeamento:

```text
aliquota_icms
    memoria_calculo["tributos"]["icms"]["aliquota"]

aliquota_fcp
    memoria_calculo["tributos"]["fcp"]["aliquota"]

aliquota_pis
    memoria_calculo["tributos"]["pis"]["aliquota"]

aliquota_cofins
    memoria_calculo["tributos"]["cofins"]["aliquota"]

aliquota_ipi
    memoria_calculo["tributos"]["ipi"]["aliquota"]
```

Converter:

```text
string -> Decimal
None -> None
```

Motivo:

A memória representa a alíquota efetivamente usada pelo cálculo.

Fallback permitido:

```text
resultado.regra.aliquota_*
```

somente se:

```text
memoria_calculo
```

não trouxer a chave esperada.

O fallback deve ser explícito e testado.

---

# 11. Redução de base de ICMS

Fonte obrigatória:

```python
resultado.memoria_calculo["reducao_base_icms"]
```

Não copiar diretamente:

```python
resultado.regra.reducao_base_icms
```

Motivo:

O motor permite:

```text
percentual_reducao_manual
```

e esse valor pode substituir a redução da regra.

Portanto o snapshot precisa guardar o valor efetivamente utilizado.

---

# 12. Diferimento

Fonte preferencial:

```python
resultado.memoria_calculo["diferimento"]["percentual"]
```

Fallback:

```python
resultado.regra.diferimento_icms
```

A memória é a fonte histórica prioritária.

---

# 13. Regra fiscal

Fonte:

```python
resultado.regra
```

Campos:

```text
regra_fiscal_id_original
    resultado.regra.pk

regra_fiscal_codigo
    resultado.regra.codigo_interno

regra_fiscal_descricao
    representação estável da regra
```

Não usar `str(regra)` se ele incluir valores potencialmente mutáveis ou texto não controlado.

Preferência:

```text
nome/título explícito do model
```

Caso não exista, usar `codigo_interno` como descrição mínima.

---

# 14. CFOP e códigos tributários

Fonte:

```python
resultado.regra
```

Mapear a regra efetivamente selecionada:

```text
cfop
cst_icms
csosn
cst_pis
cst_cofins
cst_ipi
beneficio_fiscal
```

Nunca buscar novamente uma `RegraFiscal` pelo produto durante a persistência.

---

# 15. Produto fiscal

Fonte:

```text
produto_fiscal resolvido
```

Usar para snapshot de:

```text
origem_mercadoria
NCM
CEST
```

A resolução deve ocorrer antes da construção do DTO.

O service de snapshot recebe:

```text
produto_fiscal
```

já resolvido.

Ele não deve chamar automaticamente:

```python
resolver_produto_fiscal()
```

dentro da função pura de construção.

---

# 16. Estado válido do cálculo

O snapshot só pode ser construído quando:

```python
resultado.calculado is True
```

e:

```python
resultado.erros == ()
```

Estados como:

```text
REGRA_NAO_ENCONTRADA
REGRA_AMBIGUA
CONTEXTO_INVALIDO
PARAMETROS_INCOMPLETOS
```

não podem gerar snapshot definitivo.

Observação:

`PARAMETROS_INCOMPLETOS` deve ser tratado como bloqueante para venda fiscal, mesmo quando não existir entrada em `erros`.

---

# 17. Avisos

`resultado.avisos` não bloqueiam por padrão.

Porém:

```text
aliquota não informada
```

gera aviso e tributo zero.

Para emissão fiscal operacional, precisamos decidir se determinadas ausências de alíquota são aceitáveis conforme CST/CSOSN.

Essa regra não deverá ser inventada pelo snapshot service.

O snapshot service apenas recebe um resultado já considerado apto pelo pipeline fiscal.

---

# 18. API mínima — Construção do item

```python
def construir_dados_item_venda_fiscal(
    *,
    item_venda,
    contexto_tributario,
    contexto_calculo,
    produto_fiscal,
    resultado_calculo,
    configuracao_fiscal_id_original=None,
) -> DadosItemVendaFiscal:
    ...
```

Responsabilidade:

```text
transformação pura
```

Não grava banco.

Não chama estoque.

Não chama caixa.

Não altera Venda.

---

# 19. API mínima — Persistência do item

```python
def persistir_item_venda_fiscal(
    *,
    item_venda,
    dados: DadosItemVendaFiscal,
) -> ItemVendaFiscal:
    ...
```

Regras:

```text
se item já possui fiscal:
    erro

não usar update_or_create
não sobrescrever snapshot existente
```

---

# 20. API mínima — Consolidação da venda

```python
def consolidar_dados_venda_fiscal(
    *,
    venda,
    contexto_tributario,
    snapshots_itens,
    configuracao_fiscal_id_original=None,
) -> DadosVendaFiscal:
    ...
```

Totais:

```text
total_base_operacao
    soma item.base_operacao

total_base_icms
    soma item.base_icms

total_icms
    soma item.valor_icms

total_fcp
    soma item.valor_fcp

total_base_pis
    soma item.base_pis

total_pis
    soma item.valor_pis

total_base_cofins
    soma item.base_cofins

total_cofins
    soma item.valor_cofins

total_base_ipi
    soma item.base_ipi

total_ipi
    soma item.valor_ipi

total_tributos
    soma item.valor_total_tributos
```

Não recalcular tributos no consolidado.

---

# 21. API mínima — Persistência da venda

```python
def persistir_venda_fiscal(
    *,
    venda,
    dados: DadosVendaFiscal,
) -> VendaFiscal:
    ...
```

Regras:

```text
se venda já possui fiscal:
    erro
```

Não usar:

```python
update_or_create()
```

---

# 22. API orquestradora futura

Não implementar ainda nesta primeira aplicação do service puro, mas reservar contrato para:

```python
def construir_e_persistir_snapshot_fiscal_venda(
    *,
    venda,
    contexto_operacional,
    uf_destino,
) -> VendaFiscal:
    ...
```

Essa função será a ponte com `finalizar_venda()`.

Ela será criada ou integrada somente após homologação isolada dos builders/persistors.

---

# 23. Idempotência

Snapshot definitivo não é idempotência por sobrescrita.

Contrato:

```text
primeira persistência
    sucesso

segunda persistência
    erro de domínio
```

Isso protege histórico.

---

# 24. Atomicidade

As funções isoladas não precisam abrir nova transação.

Na integração futura:

```text
finalizar_venda()
```

já possui:

```python
@transaction.atomic
```

O snapshot será persistido dentro dessa transação.

Evitar transações internas desnecessárias.

---

# 25. Quantização

Não recalcular valores tributários.

Os valores do motor já estão quantizados.

Na conversão de alíquotas vindas de `memoria_calculo`:

```python
Decimal(valor)
```

sem nova regra de arredondamento.

---

# 26. Erros de domínio propostos

Usar `ValidationError` nesta fase, consistente com o projeto.

Mensagens conceituais:

```text
"O cálculo tributário não está apto para gerar snapshot fiscal."

"O item já possui snapshot fiscal."

"A venda já possui snapshot fiscal."

"O resultado fiscal não possui regra efetiva."

"A memória de cálculo fiscal está inconsistente."
```

---

# 27. Testes obrigatórios — Builder de item

1. copia campos comerciais;
2. copia bases e valores do resultado;
3. copia alíquotas da memória;
4. aceita alíquota `None`;
5. usa redução efetiva da memória;
6. usa diferimento efetivo da memória;
7. copia regra efetiva;
8. copia classificação do produto resolvido;
9. rejeita resultado não calculado;
10. rejeita resultado com erros;
11. não consulta banco para reconstruir regra;
12. não persiste nada.

---

# 28. Testes obrigatórios — Persistência

1. cria `ItemVendaFiscal`;
2. rejeita segundo snapshot do mesmo item;
3. cria `VendaFiscal`;
4. rejeita segundo snapshot da mesma venda;
5. não usa `update_or_create`;
6. não movimenta caixa;
7. não movimenta estoque.

---

# 29. Testes obrigatórios — Consolidação

1. soma bases;
2. soma ICMS;
3. soma FCP;
4. soma PIS;
5. soma COFINS;
6. soma IPI;
7. soma total de tributos;
8. preserva contexto da venda;
9. não recalcula imposto.

---

# 30. Decisões finais da matriz

### Fonte de regime tributário

```text
Contexto tributário
```

### Fonte de UF origem/destino

```text
Contexto tributário
```

### Fonte de contribuinte/consumidor final

```text
Contexto tributário
```

### Fonte do CFOP/CST/CSOSN efetivos

```text
Regra efetiva presente em ResultadoCalculoTributario
```

### Fonte das alíquotas

```text
memoria_calculo["tributos"]
```

com fallback explícito para `resultado.regra`.

### Fonte da redução

```text
memoria_calculo["reducao_base_icms"]
```

### Fonte do diferimento

```text
memoria_calculo["diferimento"]["percentual"]
```

### Fonte das bases/valores

```text
ResultadoCalculoTributario
```

### Consulta adicional ao banco

O builder puro:

```text
não
```

A preparação anterior pode resolver:

```text
contexto
produto fiscal
regra
```

### API mínima

```text
builder item
persistor item
consolidador venda
persistor venda
```

---

# 31. Gate para Aplicação 180

A Aplicação 180 poderá criar:

```text
pdv/services/fiscal/__init__.py
pdv/services/fiscal/snapshot_venda.py
pdv/tests/services/fiscal/test_snapshot_venda.py
```

Não deverá alterar:

```text
pdv/services/vendas/finalizacao.py
estoque
caixa
views
templates
models
migrations
```

---

# 32. Critério de aprovação da Aplicação 180

Somente aprovar se:

```text
manage.py check = OK
makemigrations --check --dry-run = No changes detected
testes novos = OK
regressão snapshot/motor fiscal = OK
git diff --check = OK
```

E o serviço continuar completamente isolado do fluxo de finalização.

---

# 33. Próximo passo

```text
Aplicação 180
Implementar serviço puro de construção e persistência do snapshot fiscal
```

Depois:

```text
Diagnóstico/Validação 181
Homologar service isoladamente
```

Somente depois:

```text
Integração com finalizar_venda()
```
