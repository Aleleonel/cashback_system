# PDV-04 - Correcao de pagamentos parciais e mistos

## Regra funcional

Todas as formas de pagamento podem quitar apenas parte da venda:

- dinheiro;
- PIX;
- cartao de debito;
- cartao de credito;
- demais formas ativas.

O operador pode adicionar varias linhas ate a soma atingir o total liquido.

## Comportamento da tela

- O campo `Valor` representa a parte atribuida a forma.
- O campo `Recebido` fica editavel para todas as formas.
- Para PIX, debito e credito, editar `Recebido` atualiza o `Valor`.
- Para formas sem troco, `Recebido` deve ser igual ao `Valor`.
- Ao adicionar nova linha, o sistema preenche automaticamente o restante.
- Falta ou excesso bloqueia a finalizacao.
- Somente dinheiro pode possuir recebido maior e gerar troco.

## Backend

O backend ja aceita lista de pagamentos, registra cada linha e exige que a soma
seja igual ao total da venda. Nenhuma migration foi necessaria.

## Homologacao visual obrigatoria

1. PIX R$ 40,00 + debito R$ 60,00 em venda de R$ 100,00.
2. Credito R$ 30,00 + PIX R$ 20,00 + dinheiro R$ 50,00.
3. Debito parcial seguido de credito parcial.
4. Dinheiro parcial com valor recebido igual.
5. Dinheiro com troco.
6. Tentativa com valor faltante.
7. Tentativa com valor excedente.
8. Remocao de uma linha e recalculo do restante.
