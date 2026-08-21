from pathlib import Path

from django.test import SimpleTestCase


class HomologacaoDocumentoFiscalUI194GTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path(
            "fiscal/views_homologacao.py"
        ).read_text(encoding="utf-8")
        cls.urls = Path(
            "fiscal/urls.py"
        ).read_text(encoding="utf-8")
        cls.template = Path(
            "fiscal/templates/fiscal/"
            "homologacao_documento_fiscal.html"
        ).read_text(encoding="utf-8")
        cls.detalhe = Path(
            "pdv/templates/pdv/detalhe_venda.html"
        ).read_text(encoding="utf-8")
        cls.finalizacao = Path(
            "pdv/services/vendas/finalizacao.py"
        ).read_text(encoding="utf-8")

    def test_rotas_get_e_post_existem(self):
        self.assertIn(
            'name="homologacao_documento_fiscal"',
            self.urls,
        )
        self.assertIn(
            'name="preparar_documento_fiscal_homologacao"',
            self.urls,
        )

    def test_permissoes_estao_separadas(self):
        self.assertIn(
            "@require_permission(PERMISSAO_PDV_VISUALIZAR)",
            self.views,
        )
        self.assertIn(
            "@require_permission(PERMISSAO_PDV_OPERAR)",
            self.views,
        )
        self.assertIn("@require_GET", self.views)
        self.assertIn("@require_POST", self.views)

    def test_consulta_isola_matriz_e_lojas(self):
        self.assertIn('matriz=matriz', self.views)
        self.assertIn('loja__in=lojas', self.views)
        self.assertIn('uuid=venda_uuid', self.views)

    def test_parametros_de_homologacao_sao_fixos(self):
        self.assertIn(
            "MODELO_HOMOLOGACAO = ModeloDocumentoFiscal.NFCE",
            self.views,
        )
        self.assertIn(
            "AMBIENTE_HOMOLOGACAO = "
            "AmbienteDocumentoFiscal.HOMOLOGACAO",
            self.views,
        )
        self.assertIn("SERIE_HOMOLOGACAO = 1", self.views)

    def test_view_nao_cria_documento_diretamente(self):
        self.assertNotIn(
            "DocumentoFiscal.objects.create(",
            self.views,
        )
        self.assertNotIn(
            "SequenciaDocumentoFiscal",
            self.views,
        )
        self.assertIn(
            "preparar_documento_fiscal(",
            self.views,
        )

    def test_snapshot_e_itens_sao_somente_consultados(self):
        self.assertIn(
            "VendaFiscal.objects.filter(venda=venda).first()",
            self.views,
        )
        self.assertIn(
            "ItemVendaFiscal.objects",
            self.views,
        )
        self.assertNotIn(
            "VendaFiscal.objects.create",
            self.views,
        )
        self.assertNotIn(
            "ItemVendaFiscal.objects.create",
            self.views,
        )

    def test_template_exibe_gate_operacional(self):
        for termo in (
            "Homologação fiscal",
            "Snapshot fiscal",
            "Itens fiscais",
            "Documento fiscal",
            "Preparar documento fiscal",
            'documento.status == "preparado"',
            "SEFAZ",
        ):
            self.assertIn(termo, self.template)

    def test_template_nao_exibe_xml_bruto(self):
        self.assertNotIn(
            "{{ documento.xml_rascunho",
            self.template,
        )
        self.assertNotIn(
            "{{ documento.xml_assinado",
            self.template,
        )
        self.assertNotIn(
            "{{ documento.xml_autorizado",
            self.template,
        )

    def test_detalhe_da_venda_possui_acesso_fiscal(self):
        self.assertIn(
            "fiscal:homologacao_documento_fiscal",
            self.detalhe,
        )
        self.assertIn(
            'data-pdv-fiscal-homologacao="194g"',
            self.detalhe,
        )

    def test_nao_existe_acao_de_autorizacao(self):
        self.assertNotIn(
            "def autorizar_documento_fiscal",
            self.views,
        )
        self.assertNotIn(
            "Autorizar NFC-e",
            self.template,
        )
        self.assertNotIn(
            "Transmitir",
            self.template,
        )

    def test_finalizacao_nao_recebeu_codigo_de_homologacao(self):
        self.assertNotIn(
            "views_homologacao",
            self.finalizacao,
        )
        self.assertNotIn(
            "preparar_documento_fiscal_homologacao",
            self.finalizacao,
        )