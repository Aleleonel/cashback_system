# PDV-05C.1C - Projeto 182B - Contrato de Integracao do Snapshot Fiscal

## Estado

Projeto arquitetural. Nenhuma integracao funcional e realizada por este documento.

## Fontes autoritativas

- Matriz: `venda.matriz`.
- Loja: `venda.loja`.
- Configuracao fiscal: `get_configuracao_fiscal_matriz(matriz=venda.matriz)`.
- Contexto tributario: `construir_contexto_tributario(...)`.
- Resolucao do produto: `resolver_produto_fiscal(produto=..., contexto=...)`.
- Calculo: `calcular_tributos(ContextoCalculoTributario(...))`.
- Snapshot: services existentes em `pdv/services/fiscal/snapshot_venda.py`.

## UF destino

Status: **BLOQUEANTE: sem fonte operacional confiavel detectada**

BLOQUEIO ARQUITETURAL: o modelo operacional inspecionado nao oferece fonte confiavel de UF destino.

A integracao funcional nao deve inventar UF.

## Caracterizacao ICMS / consumidor final

Enquanto a Venda ou o Cliente nao possuirem caracterizacao fiscal especifica:

- `contribuinte_icms=None`;
- `consumidor_final=None`.

Isso delega aos defaults de `ConfiguracaoFiscalMatriz` ja implementados por
`construir_contexto_tributario`.

Nao inferir contribuinte de ICMS apenas pela existencia de CPF ou CNPJ.

## Assinatura minima

``python
def preparar_e_persistir_snapshot_fiscal_venda(
    *,
    venda,
    uf_destino,
):
    ...
``

A matriz e a loja nao devem ser argumentos duplicados: pertencem a Venda e devem
ser obtidas de `venda.matriz` e `venda.loja`.

## Ordem transacional

1. lock da Venda;
2. associar cliente consumidor;
3. validar fechamento com suporte fiscal explicitamente habilitado;
4. para Venda FISCAL, preparar e persistir snapshot;
5. confirmar reservas/estoque;
6. registrar caixa;
7. finalizar modelo;
8. registrar auditoria.

O snapshot permanece dentro da mesma `transaction.atomic` de `finalizar_venda`.

## Invariantes

- NAO_FISCAL nao executa pipeline fiscal.
- FISCAL nao chega ao estoque se o fiscal falhar.
- FISCAL nao chega ao caixa se o fiscal falhar.
- Snapshot preexistente nao e sobrescrito.
- Falha posterior ao snapshot causa rollback transacional.
- Alteracoes futuras em Produto/RegraFiscal nao alteram o historico.
- Nenhum documento fiscal externo e emitido nesta etapa.

## Proxima etapa

Somente se a UF destino estiver resolvida de forma confiavel:
**Aplicacao 183 - Integracao controlada do pipeline fiscal ao finalizar_venda().**

Se a UF destino estiver bloqueante, criar primeiro uma etapa especifica para
formalizar a origem da UF no dominio operacional.
