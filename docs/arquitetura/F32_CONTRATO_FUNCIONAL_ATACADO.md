# PRO Cash — F32 | Contrato funcional obrigatório do Atacado
Data: 2026-11-06
Estado: aprovado pelo responsável funcional; implementação e validação pendentes de auditoria.

## 1. Orçamento e titularidade
- Orçamento nasce com cliente identificado, vendedor responsável, itens, quantidades, preços, descontos, validade e forma/condições de pagamento.
- Vendedor responsável pode editar o orçamento enquanto não houver pedido pago consolidado, com histórico auditável de revisões.
- Durante a validade, outros vendedores não podem interferir ou assumir a cotação sem autorização expressa, rastreável.
- Expiração não transfere automaticamente titularidade nem direito a comissão; exceções precisam de política explícita.

## 2. Conversão e venda
- Aceite do cliente e confirmação da operação de pagamento são requisitos para transformar orçamento em pedido consolidado.
- Em parcelamento, confirmação da operação/compromisso de pagamento não equivale à liquidação de todas as parcelas.
- Conversão deve ser atômica, idempotente e impedir pedidos, títulos, estoque ou comissões duplicados.
- Pedido consolidado compõe vendas do dia e integração operacional aplicável.

## 3. Financeiro, caixa e resultado
- Registrar integralmente o direito a receber, vencimentos e situação de cada parcela.
- Registrar separadamente pagamentos efetivamente recebidos, taxas financeiras, descontos, inadimplência e conciliação.
- Caixa e fechamento do dia incluem apenas movimentos financeiros efetivos; não antecipar parcelas futuras.
- Relatórios e DRE devem diferenciar competência e caixa, sem dupla contabilização.

## 4. Comissões
- Comissão calculada integralmente na consolidação da venda, conforme política vigente, atribuída ao vendedor titular do orçamento.
- Parcelamento ou atraso de pagamento do cliente não fraciona nem posterga automaticamente a comissão.
- Pagamento da comissão segue a competência e calendário definidos pela empresa, independentemente do calendário das parcelas do cliente.
- Cancelamento, devolução, fraude e estorno demandam tratamento específico, auditável e juridicamente válido; não presumir desconto automático de comissão.

## 5. Fiscal
- Pedido consolidado deve ficar apto à emissão fiscal adequada: NF-e 55 ou NFC-e 65, segundo natureza da operação e exigências legais.
- Preservar os módulos fiscais já existentes; emissão real depende de validações fiscais e integração aplicável.

## 6. Critério de aceite
Diagnóstico -> aplicação em branch própria (nunca diretamente em develop) -> testes automatizados -> validação visual -> teste operacional real -> checkpoint.
Verificar cenário à vista, parcelado, pagamento parcial quando permitido, duplicidade de conversão, vencimento/proteção do orçamento, comissão integral, taxas, fechamento, cancelamento/estorno e aptidão fiscal.

## 7. Próxima ação
Executar auditoria F32H somente leitura e examinar F32H_RESULTADO_UNIFICADO.txt antes de implementar alterações. NFS-e F33 suspensa até conclusão integral da F32.
