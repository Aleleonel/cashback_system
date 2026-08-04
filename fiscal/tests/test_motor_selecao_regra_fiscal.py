from datetime import date, timedelta

from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.domain import ContextoSelecaoFiscal, EstadoSelecaoFiscal
from fiscal.models import CSTICMS, RegraFiscal
from fiscal.services_motor_selecao import selecionar_regra


class MotorSelecaoFiscalTests(TestCase):
    def setUp(self):
        RegraFiscal.objects.all().delete()
        self.cst = CSTICMS.objects.filter(codigo="00").first()
        self.matriz = Matriz.objects.create(nome="Matriz Motor Fiscal")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Motor Fiscal",
        )

    def contexto(self, **extras):
        dados = {
            "data_operacao": date.today(),
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "uf_origem": "sp",
            "uf_destino": "sp",
            "matriz": self.matriz,
            "loja": self.loja,
        }
        dados.update(extras)
        return ContextoSelecaoFiscal(**dados)

    def criar_regra(self, codigo, prioridade=100, **extras):
        dados = {
            "codigo_interno": codigo,
            "nome": codigo,
            "prioridade": prioridade,
            "ativo": True,
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "cst_icms": self.cst,
        }
        dados.update(extras)
        return RegraFiscal.objects.create(**dados)

    def test_contexto_invalido_retorna_estado(self):
        resultado = selecionar_regra(
            self.contexto(uf_origem="")
        )
        self.assertEqual(
            resultado.estado,
            EstadoSelecaoFiscal.CONTEXTO_INVALIDO,
        )

    def test_sem_regra_retorna_estado_estruturado(self):
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(
            resultado.estado,
            EstadoSelecaoFiscal.NAO_ENCONTRADA,
        )
        self.assertIn("etapas", resultado.memoria_decisao)

    def test_prioridade_menor_vence(self):
        self.criar_regra("REG-100", prioridade=100)
        melhor = self.criar_regra("REG-010", prioridade=10)
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(resultado.regra, melhor)
        self.assertEqual(resultado.prioridade, 10)

    def test_regra_de_loja_vence_global(self):
        self.criar_regra("REG-GLOBAL", prioridade=10)
        especifica = self.criar_regra(
            "REG-LOJA",
            prioridade=10,
            matriz=self.matriz,
            loja=self.loja,
        )
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(resultado.regra, especifica)

    def test_regra_de_matriz_vence_global(self):
        self.criar_regra("REG-GLOBAL", prioridade=10)
        especifica = self.criar_regra(
            "REG-MATRIZ",
            prioridade=10,
            matriz=self.matriz,
        )
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(resultado.regra, especifica)

    def test_regra_fora_da_vigencia_e_ignorada(self):
        self.criar_regra(
            "REG-VENCIDA",
            vigencia_fim=date.today() - timedelta(days=1),
        )
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(
            resultado.estado,
            EstadoSelecaoFiscal.NAO_ENCONTRADA,
        )

    def test_regra_inativa_e_ignorada(self):
        self.criar_regra("REG-INATIVA", ativo=False)
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(
            resultado.estado,
            EstadoSelecaoFiscal.NAO_ENCONTRADA,
        )

    def test_ambiguidade_retorna_conflito(self):
        self.criar_regra("REG-A", prioridade=10)
        self.criar_regra("REG-B", prioridade=10)
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(
            resultado.estado,
            EstadoSelecaoFiscal.AMBIGUA,
        )
        self.assertEqual(
            set(resultado.regras_conflitantes),
            {"REG-A", "REG-B"},
        )

    def test_memoria_decisao_identifica_vencedora(self):
        regra = self.criar_regra(
            "REG-MEMORIA",
            prioridade=20,
            uf_origem="SP",
        )
        resultado = selecionar_regra(self.contexto())
        self.assertEqual(resultado.regra, regra)
        self.assertEqual(
            resultado.memoria_decisao["regra_selecionada"],
            "REG-MEMORIA",
        )
