from datetime import date
from decimal import Decimal

from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.domain import (
    ContextoSelecaoFiscal,
    EstadoSelecaoFiscal,
    ResultadoSelecaoFiscal,
)
from fiscal.domain.calculo_tributario import (
    ContextoCalculoTributario,
    EstadoCalculoTributario,
)
from fiscal.models import CSTICMS, RegraFiscal
from fiscal.services_motor_selecao import (
    selecionar_regra,
)
from fiscal.services_motor_tributario import (
    calcular_tributos,
)


class MotorTributarioTests(TestCase):
    def setUp(self):
        RegraFiscal.objects.all().delete()

        self.cst = CSTICMS.objects.filter(
            codigo="00"
        ).first()
        self.matriz = Matriz.objects.create(
            nome="Matriz Motor Tributario",
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Motor Tributario",
        )

    def criar_regra(self, **extras):
        dados = {
            "codigo_interno": "REG-CALCULO",
            "nome": "Regra de calculo",
            "prioridade": 10,
            "ativo": True,
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "uf_origem": "SP",
            "uf_destino": "SP",
            "cst_icms": self.cst,
            "aliquota_icms": Decimal("18"),
            "aliquota_fcp": Decimal("2"),
            "aliquota_pis": Decimal("1.65"),
            "aliquota_cofins": Decimal("7.60"),
            "aliquota_ipi": Decimal("5"),
        }
        dados.update(extras)
        return RegraFiscal.objects.create(**dados)

    def selecionar(self):
        return selecionar_regra(
            ContextoSelecaoFiscal(
                data_operacao=date.today(),
                regime_tributario="normal",
                tipo_operacao="saida",
                finalidade_operacao="venda",
                uf_origem="SP",
                uf_destino="SP",
                matriz=self.matriz,
                loja=self.loja,
            )
        )

    def contexto_calculo(self, selecao, **extras):
        dados = {
            "resultado_selecao_fiscal": selecao,
            "valor_produtos": Decimal("100.00"),
            "quantidade": Decimal("1"),
            "desconto": Decimal("0"),
            "acrescimo": Decimal("0"),
            "frete": Decimal("0"),
            "seguro": Decimal("0"),
            "outras_despesas": Decimal("0"),
        }
        dados.update(extras)
        return ContextoCalculoTributario(**dados)

    def test_calcula_tributos_percentuais(self):
        self.criar_regra()
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.estado,
            EstadoCalculoTributario.CALCULADO,
        )
        self.assertEqual(
            resultado.valor_icms,
            Decimal("18.00"),
        )
        self.assertEqual(
            resultado.valor_fcp,
            Decimal("2.00"),
        )
        self.assertEqual(
            resultado.valor_pis,
            Decimal("1.65"),
        )
        self.assertEqual(
            resultado.valor_cofins,
            Decimal("7.60"),
        )
        self.assertEqual(
            resultado.valor_ipi,
            Decimal("5.00"),
        )
        self.assertEqual(
            resultado.valor_total_tributos,
            Decimal("34.25"),
        )

    def test_desconto_reduz_base(self):
        self.criar_regra()
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar(),
                desconto=Decimal("10.00"),
            )
        )

        self.assertEqual(
            resultado.base_operacao,
            Decimal("90.00"),
        )
        self.assertEqual(
            resultado.valor_icms,
            Decimal("16.20"),
        )

    def test_frete_e_despesas_aumentam_base(self):
        self.criar_regra()
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar(),
                frete=Decimal("10"),
                seguro=Decimal("2"),
                outras_despesas=Decimal("3"),
            )
        )

        self.assertEqual(
            resultado.base_operacao,
            Decimal("115.00"),
        )

    def test_reducao_base_icms(self):
        self.criar_regra(
            reducao_base_icms=Decimal("50")
        )
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.base_icms,
            Decimal("50.00"),
        )
        self.assertEqual(
            resultado.valor_icms,
            Decimal("9.00"),
        )

    def test_diferimento_icms(self):
        self.criar_regra(
            diferimento_icms=Decimal("50")
        )
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.valor_icms_bruto,
            Decimal("18.00"),
        )
        self.assertEqual(
            resultado.valor_icms_diferido,
            Decimal("9.00"),
        )
        self.assertEqual(
            resultado.valor_icms,
            Decimal("9.00"),
        )

    def test_float_e_rejeitado(self):
        self.criar_regra()
        contexto = ContextoCalculoTributario(
            resultado_selecao_fiscal=(
                self.selecionar()
            ),
            valor_produtos=100.0,
        )
        resultado = calcular_tributos(contexto)

        self.assertEqual(
            resultado.estado,
            EstadoCalculoTributario.CONTEXTO_INVALIDO,
        )

    def test_regra_nao_encontrada_bloqueia(self):
        selecao = ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.NAO_ENCONTRADA,
        )
        resultado = calcular_tributos(
            self.contexto_calculo(selecao)
        )

        self.assertEqual(
            resultado.estado,
            EstadoCalculoTributario.REGRA_NAO_ENCONTRADA,
        )

    def test_regra_ambigua_bloqueia(self):
        selecao = ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.AMBIGUA,
            regras_conflitantes=(
                "REG-A",
                "REG-B",
            ),
        )
        resultado = calcular_tributos(
            self.contexto_calculo(selecao)
        )

        self.assertEqual(
            resultado.estado,
            EstadoCalculoTributario.REGRA_AMBIGUA,
        )

    def test_aliquotas_ausentes_geram_parametros_incompletos(self):
        self.criar_regra(
            aliquota_icms=None,
            aliquota_fcp=None,
            aliquota_pis=None,
            aliquota_cofins=None,
            aliquota_ipi=None,
        )
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.estado,
            EstadoCalculoTributario.PARAMETROS_INCOMPLETOS,
        )
        self.assertEqual(
            resultado.valor_total_tributos,
            Decimal("0.00"),
        )

    def test_arredondamento_half_up(self):
        self.criar_regra(
            aliquota_icms=Decimal("1.005"),
            aliquota_fcp=None,
            aliquota_pis=None,
            aliquota_cofins=None,
            aliquota_ipi=None,
        )
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.valor_icms,
            Decimal("1.01"),
        )

    def test_memoria_calculo_e_consistente(self):
        self.criar_regra()
        resultado = calcular_tributos(
            self.contexto_calculo(
                self.selecionar()
            )
        )

        self.assertEqual(
            resultado.memoria_calculo[
                "regra"
            ]["codigo"],
            "REG-CALCULO",
        )
        self.assertEqual(
            resultado.memoria_calculo[
                "valor_total_tributos"
            ],
            "34.25",
        )
