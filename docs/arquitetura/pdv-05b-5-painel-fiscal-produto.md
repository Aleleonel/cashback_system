# PDV-05B.5 - Painel Fiscal Efetivo do Produto

## Objetivo

Expor no detalhe do Produto a classificacao fiscal efetiva para uma UF de
destino informada pelo usuario, sem persistencia e sem calculo monetario.

## Fluxo

View detalhe_produto
-> montar_painel_fiscal_produto
-> construir_contexto_tributario
-> resolver_produto_fiscal
-> PainelFiscalProduto
-> template

## Regras arquiteturais

- a view coordena;
- o service decide a apresentacao;
- o Builder monta o contexto;
- o Resolver resolve a classificacao;
- o template apenas apresenta;
- a UF de destino vem da query string;
- a consulta nao persiste estado;
- models e migrations nao sao alterados.

## Estados

- contexto_incompleto;
- configuracao_fiscal_ausente;
- valida;
- incompleta;
- sem_regra;
- ambigua;
- contexto_invalido.

## Seguranca

O Produto continua sendo obtido pelo selector com filtro de Matriz.
A consulta fiscal nao altera permissoes nem cadastros.