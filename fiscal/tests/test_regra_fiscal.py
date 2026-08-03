from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario
from auditoria.models import RegistroAuditoria
from empresas.models import Loja, Matriz
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import RegraFiscalForm
from fiscal.models import CSTICMS, CSOSN, RegraFiscal
from fiscal.selectors import (
    RegraFiscalAmbiguaError,
    selecionar_regra_fiscal,
)
from fiscal.services import criar_regra_fiscal


class RegraFiscalModelTests(TestCase):
    def setUp(self):
        self.cst = CSTICMS.objects.filter(
            codigo="00"
        ).first()

    def regra_base(self, **extras):
        dados = {
            "codigo_interno": "REG-TESTE",
            "nome": "Regra de teste",
            "regime_tributario": "normal",
            "tipo_operacao": "saida",
            "finalidade_operacao": "venda",
            "uf_origem": "SP",
            "cst_icms": self.cst,
            "ativo": True,
        }
        dados.update(extras)
        return RegraFiscal(**dados)

    def test_rejeita_cst_e_csosn_simultaneos(self):
        csosn = CSOSN.objects.first()
        regra = self.regra_base(csosn=csosn)

        with self.assertRaises(ValidationError):
            regra.full_clean()

    def test_rejeita_loja_de_outra_matriz(self):
        matriz_a = Matriz.objects.create(
            nome="Matriz A"
        )
        matriz_b = Matriz.objects.create(
            nome="Matriz B"
        )
        loja = Loja.objects.create(
            matriz=matriz_b,
            nome="Loja B",
        )
        regra = self.regra_base(
            matriz=matriz_a,
            loja=loja,
        )

        with self.assertRaises(ValidationError):
            regra.full_clean()

    def test_rejeita_percentual_maior_que_cem(self):
        regra = self.regra_base(
            aliquota_icms=Decimal("101")
        )

        with self.assertRaises(ValidationError):
            regra.full_clean()

    def test_rejeita_vigencia_invertida(self):
        regra = self.regra_base(
            vigencia_inicio=date(2026, 8, 3),
            vigencia_fim=date(2026, 8, 2),
        )

        with self.assertRaises(ValidationError):
            regra.full_clean()


class RegraFiscalFormTests(TestCase):
    def test_codigo_bloqueado_na_edicao(self):
        regra = RegraFiscal.objects.first()
        self.assertIsNotNone(regra)

        form = RegraFiscalForm(instance=regra)

        self.assertTrue(
            form.fields["codigo_interno"].disabled
        )


class RegraFiscalSelectorTests(TestCase):
    def setUp(self):
        RegraFiscal.objects.all().delete()
        self.cst = CSTICMS.objects.filter(
            codigo="00"
        ).first()

    def criar_regra(
        self,
        codigo,
        prioridade,
        uf_origem="",
    ):
        return RegraFiscal.objects.create(
            codigo_interno=codigo,
            nome=codigo,
            prioridade=prioridade,
            regime_tributario="normal",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            uf_origem=uf_origem,
            cst_icms=self.cst,
            ativo=True,
        )

    def test_menor_prioridade_numerica_vence(self):
        self.criar_regra(
            "REG-HOM-ALTA",
            100,
        )
        melhor = self.criar_regra(
            "REG-HOM-BAIXA",
            10,
        )

        selecionada = selecionar_regra_fiscal(
            regime_tributario="normal",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            uf_origem="SP",
            uf_destino="SP",
        )

        self.assertEqual(selecionada, melhor)

    def test_especificidade_desempata(self):
        self.criar_regra(
            "REG-HOM-GERAL",
            10,
        )
        especifica = self.criar_regra(
            "REG-HOM-SP",
            10,
            uf_origem="SP",
        )

        selecionada = selecionar_regra_fiscal(
            regime_tributario="normal",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            uf_origem="SP",
            uf_destino="SP",
        )

        self.assertEqual(selecionada, especifica)

    def test_ambiguidade_e_explicita(self):
        self.criar_regra("REG-HOM-A", 10)
        self.criar_regra("REG-HOM-B", 10)

        with self.assertRaises(
            RegraFiscalAmbiguaError
        ):
            selecionar_regra_fiscal(
                regime_tributario="normal",
                tipo_operacao="saida",
                finalidade_operacao="venda",
                uf_origem="SP",
                uf_destino="SP",
            )


class RegraFiscalServiceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Regra Fiscal",
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="fiscal_regra_service",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.cst = CSTICMS.objects.filter(
            codigo="00"
        ).first()

    def test_criacao_registra_auditoria(self):
        regra = criar_regra_fiscal(
            dados={
                "codigo_interno": "REG-SERVICE",
                "nome": "Regra service",
                "descricao": "",
                "prioridade": 50,
                "ativo": True,
                "matriz": None,
                "loja": None,
                "regime_tributario": "normal",
                "tipo_operacao": "saida",
                "finalidade_operacao": "venda",
                "uf_origem": "SP",
                "uf_destino": "",
                "contribuinte_icms": None,
                "consumidor_final": None,
                "ncm": None,
                "cest": None,
                "cfop": None,
                "cst_icms": self.cst,
                "csosn": None,
                "cst_pis": None,
                "cst_cofins": None,
                "cst_ipi": None,
                "beneficio_fiscal": None,
                "aliquota_icms": None,
                "reducao_base_icms": None,
                "aliquota_fcp": None,
                "aliquota_mva": None,
                "aliquota_pis": None,
                "aliquota_cofins": None,
                "aliquota_ipi": None,
                "diferimento_icms": None,
                "vigencia_inicio": None,
                "vigencia_fim": None,
            },
            usuario_executor=self.usuario,
            matriz_auditoria=self.matriz,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                recurso="fiscal.regra_fiscal",
                recurso_id=regra.id,
            ).exists()
        )


class RegraFiscalViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Regra Views",
        )
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="fiscal_admin_regra",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_regra",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(
            reverse("fiscal:lista_regras_fiscais")
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "Regras fiscais",
        )

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_regras_fiscais")
            ).status_code,
            403,
        )

    def test_permissao_extra_libera_visualizacao(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:lista_regras_fiscais")
            ).status_code,
            200,
        )

    def test_criacao_exige_gerenciamento(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_regra_fiscal")
            ).status_code,
            403,
        )

        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=(
                PERMISSAO_FISCAL_GERENCIAR_CADASTROS
            ),
        )

        self.assertEqual(
            self.client.get(
                reverse("fiscal:criar_regra_fiscal")
            ).status_code,
            200,
        )
