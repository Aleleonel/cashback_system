from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from configuracoes.models import ComissaoVendedor, FechamentoComissao
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro


class F24UiProvisionamentoComissaoRedTests(TestCase):
    """
    Contrato RED F24:
    - a UI de comissoes provisiona, mas nao paga;
    - snapshot permanece imutavel;
    - titulo COMISSAO existente e reutilizado/exposto;
    - escopo vem do fechamento;
    - inelegivel/zero nao pode provisionar.
    """

    def test_view_comissoes_deve_expor_acao_provisionar_sem_motor_pagamento_paralelo(self):
        from pathlib import Path
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        template = Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")
        self.assertIn('provisionar_comissao', fonte)
        self.assertIn('gerar_titulo_financeiro_comissao', fonte)
        self.assertIn('provisionar_comissao', template)
        self.assertNotIn('registrar_baixa_financeira(', fonte)
        self.assertNotIn('registrar_baixa_financeira_com_caixa(', fonte)

    def test_ui_deve_expor_titulo_existente_em_vez_de_oferecer_nova_duplicacao(self):
        from pathlib import Path
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        template = Path("configuracoes/templates/configuracoes/comissoes.html").read_text(encoding="utf-8")
        self.assertIn('OrigemTipo.COMISSAO', fonte)
        self.assertIn('financeiro:titulo_detalhe', template)

    def test_ui_nao_deve_mutar_snapshot_para_marcar_pago_ou_provisionado(self):
        from pathlib import Path
        fonte = Path("configuracoes/views.py").read_text(encoding="utf-8")
        proibidos = [
            'comissao.elegivel =',
            'comissao.valor_comissao =',
            'ComissaoVendedor.objects.filter',
        ]
        trecho = fonte[fonte.find("def comissoes"): fonte.find("def comissoes") + 12000]
        for item in proibidos:
            self.assertNotIn(item, trecho)

    def test_servico_continua_com_contrato_minimo_sem_plano_conta_obrigatorio(self):
        import inspect
        from configuracoes.services_comissoes import gerar_titulo_financeiro_comissao
        assinatura = inspect.signature(gerar_titulo_financeiro_comissao)
        self.assertEqual(
            list(assinatura.parameters),
            ["comissao", "vencimento", "usuario", "request"],
        )