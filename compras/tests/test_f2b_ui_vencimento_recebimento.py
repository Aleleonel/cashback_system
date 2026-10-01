from pathlib import Path
from django.conf import settings

from django import forms
from django.test import SimpleTestCase

from compras.forms import RecebimentoCompraForm


class F2BRecebimentoVencimentoUIContractTest(SimpleTestCase):
    def test_form_expoe_vencimento_financeiro_obrigatorio_com_widget_date(self):
        campos = RecebimentoCompraForm.base_fields
        self.assertIn("vencimento_financeiro", campos)
        campo = campos["vencimento_financeiro"]
        self.assertTrue(campo.required)
        self.assertIsInstance(campo, forms.DateField)
        self.assertEqual(campo.widget.input_type, "date")

    def test_view_encaminha_vencimento_estruturado_ao_servico(self):
        conteudo = Path("compras/views.py").read_text(encoding="utf-8")
        self.assertIn(
            "vencimento_financeiro=form.cleaned_data['vencimento_financeiro']",
            conteudo,
        )

    def test_template_nao_trata_vencimento_como_item_e_o_exibe_em_informacoes(self):
        conteudo = Path(
            "compras/templates/compras/pedidos/receber.html"
        ).read_text(encoding="utf-8")
        self.assertIn('field.name != "vencimento_financeiro"', conteudo)
        self.assertIn("form.vencimento_financeiro", conteudo)
        self.assertIn("form.vencimento_financeiro", conteudo)
    def test_recebimento_usa_modal_profissional_sem_confirm_nativo(self):
        template = (
            Path(settings.BASE_DIR)
            / 'compras/templates/compras/pedidos/receber.html'
        )
        conteudo = template.read_text(encoding='utf-8')
        self.assertNotIn("confirm('Confirmar o recebimento", conteudo)
        self.assertIn('id="modal-confirmar-recebimento"', conteudo)
        self.assertIn('data-bs-toggle="modal"', conteudo)
        self.assertIn('data-bs-target="#modal-confirmar-recebimento"', conteudo)
        self.assertIn('id="confirmar-recebimento-final"', conteudo)
        self.assertIn('Resumo do recebimento', conteudo)
        self.assertIn('Vencimento', conteudo)
