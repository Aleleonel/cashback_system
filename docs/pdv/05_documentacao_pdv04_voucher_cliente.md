# PDV-04 - Correcao de voucher vinculado ao cliente

## Regra

O PDV nao sugere vouchers genericos.

A area Beneficios somente sugere voucher valido quando o voucher esta
explicitamente vinculado ao cliente selecionado:

`voucher.cliente_id == venda.cliente_id`

Voucher sem cliente vinculado continua podendo ser usado pela digitacao manual
do codigo, desde que passe pelas validacoes existentes.

## Homologacao

1. Sem cliente: nenhum voucher sugerido.
2. Cliente sem voucher vinculado: nenhum voucher sugerido.
3. Cliente com voucher valido vinculado: voucher exibido em Beneficios.
4. Voucher generico ativo: nao sugerido.
5. Codigo manual valido: aplicado normalmente.
6. Codigo manual invalido: mensagem de erro.

## Sem alteracoes

Models, migrations, estoque, caixa, cashback e finalizacao da venda.
