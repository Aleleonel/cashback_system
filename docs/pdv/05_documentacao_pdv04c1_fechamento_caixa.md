# PDV-04C.1 - Fechamento de Caixa

Data de aplicacao: 20260730_194344

## Escopo

- regra canonica de fechamento da sessao;
- calculo por movimentos persistidos;
- bloqueio de vendas pendentes;
- fechamento transacional;
- views GET e POST;
- permissao `pdv.fechar_caixa`;
- template de conferencia;
- navegacao no PDV;
- auditoria;
- testes de contrato.

## Arquitetura

O fechamento da sessao foi implementado em
`pdv/services/vendas/caixa.py`.

O fechamento da venda permanece em
`pdv/services/vendas/fechamento.py`.

Nenhuma migration foi criada.
