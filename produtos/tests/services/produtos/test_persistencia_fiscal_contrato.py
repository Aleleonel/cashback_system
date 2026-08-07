from pathlib import Path

from django.test import SimpleTestCase

from produtos.services.produtos.editar import CAMPOS_EDITAVEIS


CAMPOS_FISCAIS = {
    "origem_mercadoria",
    "ncm_fiscal",
    "cest",
    "cst_icms",
    "csosn",
    "cst_pis",
    "cst_cofins",
    "cst_ipi",
    "beneficio_fiscal",
    "regra_fiscal_padrao",
}


class PersistenciaFiscalProdutoContratoTest(SimpleTestCase):
    def test_campos_fiscais_estao_no_contrato_de_edicao(self):
        faltantes = CAMPOS_FISCAIS.difference(
            set(CAMPOS_EDITAVEIS)
        )

        self.assertFalse(
            faltantes,
            f"Campos fiscais ausentes: {sorted(faltantes)}",
        )

    def test_preparar_dados_preserva_campos_fiscais(self):
        raiz_produtos = Path(__file__).resolve().parents[3]
        arquivo = (
            raiz_produtos
            / "services"
            / "produtos"
            / "validacoes.py"
        )

        fonte = arquivo.read_text(encoding="utf-8")

        for campo in CAMPOS_FISCAIS:
            contrato = (
                f"'{campo}': dados.get('{campo}')"
            )

            self.assertIn(
                contrato,
                fonte,
                campo,
            )
