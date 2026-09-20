from django.test import SimpleTestCase
from financeiro.models import BaixaFinanceira, TituloFinanceiro

class ExtensaoTituloBaixaContractRedTests(SimpleTestCase):
    def test_titulo_tem_classificacao_e_referencia_manual(self):
        campos = {f.name: f for f in TituloFinanceiro._meta.fields}
        self.assertIn("plano_conta", campos)
        self.assertIn("centro_custo", campos)
        self.assertIn("entidade_nome", campos)
        self.assertIn("documento_referencia", campos)

    def test_titulo_relacoes_classificacao_usam_protect_e_sao_opcionais_no_modelo_base(self):
        campos = {f.name: f for f in TituloFinanceiro._meta.fields}
        for nome in ("plano_conta", "centro_custo"):
            self.assertIn(nome, campos)
            campo = campos[nome]
            self.assertTrue(campo.null)
            self.assertEqual(campo.remote_field.on_delete.__name__, "PROTECT")

    def test_baixa_tem_rastreabilidade_meio_liquidacao(self):
        campos = {f.name: f for f in BaixaFinanceira._meta.fields}
        self.assertIn("forma_pagamento", campos)
        self.assertIn("conta_financeira", campos)
        self.assertIn("sessao_caixa", campos)
        self.assertIn("movimentacao_caixa", campos)

    def test_baixa_relacoes_operacionais_usam_protect_e_sao_opcionais(self):
        campos = {f.name: f for f in BaixaFinanceira._meta.fields}
        for nome in ("forma_pagamento", "conta_financeira", "sessao_caixa", "movimentacao_caixa"):
            self.assertIn(nome, campos)
            campo = campos[nome]
            self.assertTrue(campo.null)
            self.assertEqual(campo.remote_field.on_delete.__name__, "PROTECT")

    def test_baixa_nao_cria_campo_de_saldo_persistido(self):
        nomes = {f.name for f in BaixaFinanceira._meta.fields}
        self.assertNotIn("saldo", nomes)
        self.assertNotIn("saldo_atual", nomes)

    def test_titulo_nao_torna_plano_obrigatorio_globalmente(self):
        # O contrato exige plano obrigatório na ENTRADA MANUAL.
        # Origens automáticas existentes não podem quebrar nesta fundação.
        campo = TituloFinanceiro._meta.get_field("plano_conta")
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)