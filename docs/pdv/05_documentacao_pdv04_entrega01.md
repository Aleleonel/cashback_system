# PDV-04 - Entrega 01 - Consolidacao da Venda

## Alteracoes implementadas

1. Criacao do Service `pdv/services/vendas/cancelamento.py`.
2. Cancelamento da venda passou a utilizar `cancelar_item_venda`.
3. Reservas de estoque passam a ser liberadas pelo fluxo oficial dos Services.
4. A view nao exclui mais diretamente itens ou pagamentos.
5. Venda cancelada preserva cliente, vendedor e itens para rastreabilidade.
6. Correcao da obtencao da venda na validacao de voucher.
7. Inclusao de `login_required` nas views de voucher e cancelamento.
8. Publicacao de `cancelar_venda` nos arquivos `__init__.py`.
9. Inclusao de testes de contrato da consolidacao.

## Responsabilidades finais

- `views.py`: HTTP, autenticacao, leitura da requisicao e resposta JSON.
- `fechamento.py`: pagamentos, beneficios e orquestracao do fechamento.
- `finalizacao.py`: estoque, caixa, estado final e auditoria.
- `cancelamento.py`: cancelamento transacional e liberacao das reservas.
- `itens.py`: alteracoes e cancelamento individual de itens.

## Arquivos alterados

- `pdv/views.py`
- `pdv/services/__init__.py`
- `pdv/services/vendas/__init__.py`

## Arquivos criados

- `pdv/services/vendas/cancelamento.py`
- `pdv/tests/test_pdv04_entrega01_consolidacao.py`

## Modelos e migrations

Nenhum Model foi alterado e nenhuma migration deve ser criada.

## Criterio para homologacao

A entrega deve passar:

- `python manage.py check`
- testes de contrato da Entrega 01;
- testes de itens;
- testes de finalizacao;
- testes web da Frente de Caixa;
- roteiro visual de cancelamento e nova venda.
