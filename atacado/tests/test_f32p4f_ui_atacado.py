"""F32P4F: contratos de interface do Atacado/PDV, sem acessar banco principal."""
from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from django.template.loader import get_template

ROOT = Path(__file__).resolve().parents[1]

class F32P4FUIContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = (ROOT / 'templates/atacado/pedidos_lista.html').read_text(encoding='utf-8-sig')
        cls.views = (ROOT / 'views.py').read_text(encoding='utf-8-sig')

    def test_template_compila(self):
        self.assertIsNotNone(get_template('atacado/pedidos_lista.html'))

    def test_rota_http_aponta_para_view_existente(self):
        url = reverse('atacado:pedido_consolidar_pdv', args=[123])
        self.assertEqual(resolve(url).url_name, 'pedido_consolidar_pdv')

    def test_acao_so_aparece_sob_condicoes_operacionais(self):
        s = self.template
        self.assertIn('F32P4E_UI_ATACADO', s)
        self.assertIn('pode_consolidar and sessao_operacional', s)
        self.assertIn('pedido.status == status_gerado', s)
        self.assertIn('pedido.tipo_emissao == tipo_nao_fiscal', s)
        self.assertIn('pedido.loja_id == sessao_operacional.caixa.loja_id', s)
        self.assertIn('pedido.venda_pdv_id', s)

    def test_modal_pagamento_csrf_e_confirmacao(self):
        s = self.template
        for token in ('f32p4e-modal', 'f32p4e-forma', 'f32p4e-parcelas',
                      'f32p4e-confirmar', "method: 'POST'", 'X-CSRFToken',
                      'forma_pagamento_id', 'valor: pedido.total', 'parcelas: Number(parcelas.value)'):
            with self.subTest(token=token):
                self.assertIn(token, s)

    def test_contexto_restringe_operador_sessao_e_formas_ativas(self):
        s = self.views
        for token in ('F32P4E_CONTEXTO_UI', 'not request.user.is_superuser',
                      'PERMISSAO_PDV_OPERAR', 'operador_abertura=request.user',
                      'status=StatusSessaoCaixa.ABERTA', 'caixa__loja__in=lojas',
                      'matriz=matriz, ativa=True'):
            with self.subTest(token=token):
                self.assertIn(token, s)

    def test_forma_de_pagamento_e_parcelas_nao_sao_livres(self):
        s = self.template
        self.assertIn('data-parcelamento=', s)
        self.assertIn('data-max=', s)
        self.assertIn('forma.selectedOptions[0]', s)
        self.assertIn('parcelas.disabled = max === 1', s)