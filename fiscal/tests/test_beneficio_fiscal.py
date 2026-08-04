from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario
from auditoria.models import RegistroAuditoria
from empresas.models import Matriz
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import BeneficioFiscalForm
from fiscal.models import BeneficioFiscal
from fiscal.selectors import get_beneficios_fiscais
from fiscal.services import criar_beneficio_fiscal


class BeneficioFiscalModelTests(TestCase):
    def test_seed_cria_seis_registros(self):
        self.assertEqual(
            BeneficioFiscal.objects.count(),
            6,
        )

    def test_normaliza_codigo_e_uf(self):
        beneficio = BeneficioFiscal(
            codigo=" ben-teste ",
            descricao="Beneficio de teste",
            uf="sp",
            tipo_beneficio=(
                BeneficioFiscal.TIPO_ISENCAO
            ),
            regime_tributario=(
                BeneficioFiscal.REGIME_TODOS
            ),
        )
        beneficio.save()

        self.assertEqual(
            beneficio.codigo,
            "BEN-TESTE",
        )
        self.assertEqual(beneficio.uf, "SP")

    def test_rejeita_percentual_invalido(self):
        with self.assertRaises(ValidationError):
            BeneficioFiscal(
                codigo="BEN-PERCENTUAL",
                descricao="Percentual invalido",
                tipo_beneficio=(
                    BeneficioFiscal.TIPO_REDUCAO_BASE
                ),
                regime_tributario=(
                    BeneficioFiscal.REGIME_NORMAL
                ),
                percentual_reducao=Decimal("101"),
            ).full_clean()

    def test_rejeita_vigencia_invertida(self):
        with self.assertRaises(ValidationError):
            BeneficioFiscal(
                codigo="BEN-VIGENCIA",
                descricao="Vigencia invalida",
                tipo_beneficio=(
                    BeneficioFiscal.TIPO_ISENCAO
                ),
                regime_tributario=(
                    BeneficioFiscal.REGIME_TODOS
                ),
                vigencia_inicio=date(2026, 8, 2),
                vigencia_fim=date(2026, 8, 1),
            ).full_clean()


class BeneficioFiscalFormTests(TestCase):
    def test_form_valido(self):
        form = BeneficioFiscalForm(
            data={
                "codigo": " ben-form ",
                "descricao": " Beneficio de formulario ",
                "uf": "sp",
                "tipo_beneficio": "reducao_base",
                "fundamento_legal": "Teste",
                "percentual_reducao": "20.0000",
                "percentual_credito": "",
                "exige_motivo_desoneracao": "",
                "motivo_desoneracao_padrao": "",
                "regime_tributario": "normal",
                "vigencia_inicio": "",
                "vigencia_fim": "",
                "ativo": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["codigo"],
            "BEN-FORM",
        )
        self.assertEqual(
            form.cleaned_data["uf"],
            "SP",
        )

    def test_codigo_bloqueado_na_edicao(self):
        form = BeneficioFiscalForm(
            instance=BeneficioFiscal.objects.first()
        )
        self.assertTrue(
            form.fields["codigo"].disabled
        )


class BeneficioFiscalSelectorTests(TestCase):
    def test_busca_codigo(self):
        self.assertTrue(
            get_beneficios_fiscais(
                busca="BEN-HOM-001"
            ).exists()
        )

    def test_filtra_uf_tipo_regime_e_ativos(self):
        self.assertTrue(
            get_beneficios_fiscais(
                uf="SP",
                tipo_beneficio="reducao_base",
                regime_tributario="normal",
                somente_ativos=True,
            ).exists()
        )


class BeneficioFiscalServiceTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Beneficio Fiscal",
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="fiscal_beneficio_service",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )

    def test_criacao_registra_auditoria(self):
        beneficio = criar_beneficio_fiscal(
            dados={
                "codigo": "BEN-SERVICE",
                "descricao": "Beneficio de servico",
                "uf": "",
                "tipo_beneficio": "isencao",
                "fundamento_legal": "Teste",
                "percentual_reducao": None,
                "percentual_credito": None,
                "exige_motivo_desoneracao": False,
                "motivo_desoneracao_padrao": "",
                "regime_tributario": "todos",
                "vigencia_inicio": None,
                "vigencia_fim": None,
                "ativo": True,
            },
            usuario_executor=self.usuario,
            matriz=self.matriz,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                recurso="fiscal.beneficio_fiscal",
                recurso_id=beneficio.id,
            ).exists()
        )


class BeneficioFiscalViewsTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz Beneficio Fiscal Views",
        )
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="fiscal_admin_beneficio",
            password="teste123",
            perfil=User.PERFIL_ADMIN_LOJA,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador = User.objects.create_user(
            username="fiscal_operador_beneficio",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )

    def test_lista_exige_login(self):
        self.assertEqual(
            self.client.get(
                reverse(
                    "fiscal:lista_beneficios_fiscais"
                )
            ).status_code,
            302,
        )

    def test_admin_visualiza_lista(self):
        self.client.force_login(self.admin)
        resposta = self.client.get(
            reverse(
                "fiscal:lista_beneficios_fiscais"
            )
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "Beneficios fiscais",
        )

    def test_operador_sem_permissao_recebe_403(self):
        self.client.force_login(self.operador)

        self.assertEqual(
            self.client.get(
                reverse(
                    "fiscal:lista_beneficios_fiscais"
                )
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
                reverse(
                    "fiscal:lista_beneficios_fiscais"
                )
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
                reverse(
                    "fiscal:criar_beneficio_fiscal"
                )
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
                reverse(
                    "fiscal:criar_beneficio_fiscal"
                )
            ).status_code,
            200,
        )
