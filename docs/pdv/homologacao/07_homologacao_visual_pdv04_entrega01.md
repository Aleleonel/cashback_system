# PDV-04 — Entrega 01 — Roteiro de Homologação Visual

## Objetivo

Homologar o fluxo consolidado da venda desde a abertura do caixa até a conclusão do pagamento.

## Pré-condições

- ambiente virtual ativo;
- servidor Django iniciado;
- usuário com matriz e loja vinculadas;
- caixa ativo e sessão aberta;
- produto ativo com preço e saldo;
- cliente CONSUMIDOR disponível;
- vendedor ativo vinculado à loja;
- formas básicas de pagamento cadastradas.

## Registro

- Data:
- Branch:
- Commit:
- Usuário:
- Loja:
- Caixa:
- Navegador:
- Resultado geral: [ ] Aprovado  [ ] Reprovado

## 1. Tela inicial

- [ ] Abre sem erro.
- [ ] Totais começam zerados.
- [ ] Não há dados residuais de venda anterior.
- [ ] Cliente e vendedor aparecem conforme o estado inicial.

Observações:

## 2. Seleção de cliente

- [ ] Pesquisa por nome funciona.
- [ ] Seleção atualiza a tela.
- [ ] Atualização da página preserva o cliente.

Observações:

## 3. Seleção de vendedor

- [ ] Pesquisa funciona.
- [ ] Seleção atualiza a tela.
- [ ] Atualização da página preserva o vendedor.

Observações:

## 4. Inclusão de produto

- [ ] Pesquisa por nome ou código funciona.
- [ ] Item é adicionado com quantidade, preço e total corretos.
- [ ] Totais gerais são recalculados.
- [ ] Atualização da página preserva o item.

Observações:

## 5. Alteração de item

- [ ] Quantidade válida recalcula o item e a venda.
- [ ] Quantidade inválida é rejeitada com mensagem clara.
- [ ] Não há alteração parcial após erro.

Observações:

## 6. Cancelamento de item

- [ ] Item deixa de compor a venda.
- [ ] Totais são recalculados.
- [ ] Reserva de estoque é liberada.
- [ ] Item não retorna após atualizar a página.

Observações:

## 7. Preparação do fechamento

- [ ] Total a pagar está correto.
- [ ] Formas de pagamento são listadas.
- [ ] Não finaliza sem cobrir o total.
- [ ] Validações aparecem de forma compreensível.

Observações:

## 8. Finalização

- [ ] Venda passa para FINALIZADA.
- [ ] Estoque é efetivado corretamente.
- [ ] Movimentação de caixa é registrada quando aplicável.
- [ ] Auditoria é registrada.
- [ ] A tela fica pronta para nova venda.

Observações:

## 9. Idempotência

- [ ] Repetir a finalização não baixa estoque novamente.
- [ ] Não duplica movimentação de caixa.
- [ ] Não duplica cashback.
- [ ] Retorno é controlado.

Observações:

## 10. Cancelamento da venda em andamento

- [ ] A venda passa para CANCELADA.
- [ ] Reservas são liberadas.
- [ ] Cliente, vendedor e itens são limpos visualmente.
- [ ] Nova venda pode ser iniciada.

Observações:

## Critérios de aprovação

- todos os testes relevantes aprovados;
- todos os cenários visuais obrigatórios aprovados;
- nenhuma duplicidade em estoque, caixa ou cashback;
- tela limpa após finalizar ou cancelar;
- transições de estado consistentes;
- documentação oficial e CHANGELOG atualizados após homologação.

## Decisão

[ ] Homologado para documentação e commit
[ ] Reprovado — retornar à implementação
