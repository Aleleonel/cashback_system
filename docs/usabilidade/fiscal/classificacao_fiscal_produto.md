# Classificacao Fiscal Efetiva do Produto

## Objetivo

O painel de classificacao fiscal efetiva mostra como o sistema interpretou os
cadastros fiscais do Produto para uma operacao especifica.

## Onde sera exibido

O painel sera apresentado na tela de detalhe do Produto, na area fiscal.

## Informacoes exibidas

- Origem da mercadoria;
- NCM;
- CEST;
- Regra Fiscal utilizada;
- CST ICMS ou CSOSN;
- CST PIS;
- CST COFINS;
- CST IPI;
- Beneficio Fiscal;
- Status;
- alertas e observacoes.

## Como a regra e escolhida

Quando o Produto possui uma Regra Fiscal padrao vinculada, ela tem precedencia.

Quando nao possui, o sistema utiliza o Motor de Selecao considerando:

- data da operacao;
- regime tributario;
- tipo e finalidade da operacao;
- UF de origem e destino;
- matriz e loja;
- NCM e CEST;
- caracteristicas do destinatario.

## Precedencia dos campos

Um campo preenchido diretamente no Produto prevalece sobre o mesmo campo da
Regra Fiscal. Quando o campo do Produto esta vazio, o sistema utiliza o valor
da regra selecionada.

## Status

### Configuracao valida

Existe regra efetiva e os campos obrigatorios para o regime foram resolvidos.

### Configuracao incompleta

Existe regra, mas faltam classificacoes ou existem alertas.

### Sem regra

Nenhuma Regra Fiscal atende ao contexto informado.

### Regra ambigua

Mais de uma regra possui a mesma prioridade e especificidade.

### Contexto invalido

Faltam dados obrigatorios para realizar a selecao.

## Simular Tributacao

A simulacao mostrara a regra utilizada, o motivo da selecao, classificacoes,
beneficio, observacoes e memoria de decisao.

Nesta fase, a simulacao nao calcula valores de impostos.