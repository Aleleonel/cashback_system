# PDV-05B.4 - Motor Tributario aplicado ao Produto

## Objetivo

Criar uma camada reutilizavel que transforme os cadastros fiscais do Produto
em uma configuracao fiscal efetiva, sem calcular valores monetarios.

## Fonte unica de selecao

A resolucao consome o Motor de Selecao existente em
`fiscal.services_motor_selecao`. A camada de Produto nao duplica filtros,
pontuacao, prioridade, desempate ou memoria de decisao.

## Contrato de entrada

A funcao `resolver_produto_fiscal` recebe:

- `produto`;
- `ContextoSelecaoFiscal`.

O contexto informa data, regime tributario, operacao, finalidade, UFs, matriz,
loja e caracteristicas do destinatario.

## Precedencia

1. A regra vinculada diretamente em `produto.regra_fiscal_padrao` prevalece.
2. Sem regra direta, o Motor de Selecao resolve a regra efetiva.
3. Campos preenchidos diretamente no Produto prevalecem sobre a RegraFiscal.
4. Campos vazios no Produto herdam a configuracao da RegraFiscal.
5. Regra historica ja vinculada ao Produto permanece legivel.
6. Novas selecoes continuam limitadas a regras ativas e vigentes.
7. Simples Nacional utiliza CSOSN.
8. Outros regimes utilizam CST ICMS.

## DTO

`ProdutoFiscalResolvido` concentra:

- classificacoes fiscais efetivas;
- regra utilizada;
- motivo da selecao;
- observacoes;
- alertas;
- memoria de decisao;
- status estruturado.

## Estados

- `valida`;
- `incompleta`;
- `sem_regra`;
- `ambigua`;
- `contexto_invalido`.

## Fora do escopo

Esta aplicacao nao:

- calcula bases;
- aplica aliquotas;
- calcula impostos;
- persiste simulacoes;
- cria migrations;
- altera o Motor Tributario monetario.