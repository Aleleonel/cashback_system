from types import SimpleNamespace

from django.test import SimpleTestCase

from pdv.services.fiscal.snapshot_venda import (
    construir_dados_item_venda_fiscal,
)
from pdv.tests.services.fiscal.test_snapshot_venda import (
    ResultadoFake,
    contexto_calculo_fake,
    contexto_tributario_fake,
    item_fake,
)
from produtos.services.fiscal.resolver_produto_fiscal import (
    ProdutoFiscalResolvido,
)


class ContratoSnapshotFiscal183C1Tests(SimpleTestCase):
    def test_snapshot_usa_campo_origem_do_resolvido_real(self):
        resultado = ResultadoFake()

        produto_fiscal = ProdutoFiscalResolvido(
            produto=SimpleNamespace(),
            origem="0",
            ncm=SimpleNamespace(
                codigo="21069090",
                descricao="NCM teste",
            ),
            cest=SimpleNamespace(
                codigo="2806100",
                descricao="CEST teste",
            ),
            regra=resultado.regra,
        )

        dados = construir_dados_item_venda_fiscal(
            item_venda=item_fake(),
            contexto_tributario=contexto_tributario_fake(),
            contexto_calculo=contexto_calculo_fake(),
            produto_fiscal=produto_fiscal,
            resultado_calculo=resultado,
        )

        self.assertEqual(
            dados.origem_mercadoria_codigo,
            "0",
        )