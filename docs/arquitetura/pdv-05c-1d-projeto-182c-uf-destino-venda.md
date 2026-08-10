# PDV-05C.1D — Projeto 182C — UF de Destino da Venda

## Decisão

A fonte autoritativa da UF de destino será `Venda.uf_destino`.

A UF é uma característica da operação fiscal concreta. Ela não deve ser
reconstruída posteriormente a partir de Loja ou Cliente.

## Campo proposto

```python
uf_destino = models.CharField(
    max_length=2,
    blank=True,
    default="",
)
```

Não usar `null=True`.

## Validação

- normalizar com `strip().upper()`;
- venda `NAO_FISCAL` pode permanecer sem UF;
- venda `FISCAL` exige UF preenchida;
- qualquer UF preenchida precisa pertencer a `UFS_VALIDAS`.

## Persistência histórica

Após a finalização, a origem histórica é a própria Venda e o snapshot
`VendaFiscal.uf_destino`.

Mesmo que futuramente Loja e Cliente recebam endereço completo, uma venda
finalizada não deverá reconstruir a UF a partir desses cadastros.

## Migration

Criar migration aditiva no app `pdv`:

```text
0006_venda_uf_destino.py
```

Sem data migration e sem alteração de registros existentes.

## Integração futura

A assinatura da orquestradora poderá ser reduzida para:

```python
def preparar_e_persistir_snapshot_fiscal_venda(*, venda):
    ...
```

Ela utilizará:

```python
venda.matriz
venda.loja
venda.uf_destino
```

e passará a UF para `construir_contexto_tributario`.

## Gate

Antes de integrar ao fechamento:

1. model + migration homologados;
2. `NAO_FISCAL` continua aceitando UF vazia;
3. `FISCAL` exige UF válida;
4. regressão atual do PDV permanece verde.

## Próxima etapa

Aplicação 183A — adicionar `Venda.uf_destino`, migration e testes de domínio.