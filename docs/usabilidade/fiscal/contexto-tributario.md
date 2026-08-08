# Contexto Tributario

O Contexto Tributario reune os dados necessarios para a selecao fiscal.

A operacao deve informar a Matriz e a UF de destino. Quando houver Loja, ela
deve pertencer a Matriz.

O sistema utiliza a Configuracao Fiscal ativa da Matriz para obter regime
tributario, UF de origem, contribuinte do ICMS e consumidor final padrao.

A ausencia de configuracao fiscal ou de UF de destino impede a construcao do
contexto e deve ser apresentada ao usuario como pendencia de configuracao ou
de preenchimento.

Esse processo nao calcula impostos.
