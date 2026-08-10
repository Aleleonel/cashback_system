from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from empresas.models import Loja, Matriz
from pdv.choices import TipoEmissaoVenda
from pdv.models import Venda
from pdv.services.vendas.validacoes import (
    validar_venda_para_finalizacao,
)


class VendaUfDestinoModelTests(SimpleTestCase):
    def venda(self, *, tipo_emissao, uf_destino=""):
        return Venda(
            tipo_emissao=tipo_emissao,
            uf_destino=uf_destino,
        )

    def test_nao_fiscal_aceita_uf_vazia_no_model(self):
        venda = self.venda(
            tipo_emissao=TipoEmissaoVenda.NAO_FISCAL,
            uf_destino="",
        )

        venda.clean()

        self.assertEqual(venda.uf_destino, "")

    def test_fiscal_rejeita_uf_vazia_no_model(self):
        venda = self.venda(
            tipo_emissao=TipoEmissaoVenda.FISCAL,
            uf_destino="",
        )

        with self.assertRaises(ValidationError) as erro:
            venda.clean()

        self.assertIn("uf_destino", erro.exception.message_dict)

    def test_fiscal_aceita_sp_e_normaliza(self):
        venda = self.venda(
            tipo_emissao=TipoEmissaoVenda.FISCAL,
            uf_destino=" sp ",
        )

        venda.clean()

        self.assertEqual(venda.uf_destino, "SP")

    def test_rejeita_uf_invalida_mesmo_nao_fiscal(self):
        venda = self.venda(
            tipo_emissao=TipoEmissaoVenda.NAO_FISCAL,
            uf_destino="XX",
        )

        with self.assertRaises(ValidationError) as erro:
            venda.clean()

        self.assertIn("uf_destino", erro.exception.message_dict)


class VendaUfDestinoValidatorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz UF Destino",
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja UF Destino",
        )

        User = get_user_model()
        self.operador = User.objects.create_user(
            username="operador_uf_destino",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
            ativo=True,
        )
        self.operador.lojas.add(self.loja)

    def criar_venda(self, *, tipo_emissao, uf_destino=""):
        return Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            operador=self.operador,
            tipo_emissao=tipo_emissao,
            uf_destino=uf_destino,
        )

    def test_validator_fiscal_exige_uf_mesmo_com_permissao_fiscal(self):
        venda = self.criar_venda(
            tipo_emissao=TipoEmissaoVenda.FISCAL,
            uf_destino="",
        )

        with self.assertRaises(ValidationError) as erro:
            validar_venda_para_finalizacao(
                venda=venda,
                permitir_fiscal=True,
            )

        self.assertIn(
            "uf_destino",
            erro.exception.message_dict,
        )

    def test_validator_nao_fiscal_nao_cria_erro_de_uf_vazia(self):
        venda = self.criar_venda(
            tipo_emissao=TipoEmissaoVenda.NAO_FISCAL,
            uf_destino="",
        )

        try:
            validar_venda_para_finalizacao(venda=venda)
        except ValidationError as erro:
            self.assertNotIn(
                "uf_destino",
                erro.message_dict,
            )
    def test_validator_normaliza_uf_fiscal(self):
        venda = self.criar_venda(
            tipo_emissao=TipoEmissaoVenda.FISCAL,
            uf_destino=" sp ",
        )

        try:
            validar_venda_para_finalizacao(
                venda=venda,
                permitir_fiscal=True,
            )
        except ValidationError:
            # A venda de teste nao possui todos os requisitos comerciais
            # de finalizacao. O contrato deste teste e somente a
            # normalizacao operacional da UF.
            pass

        self.assertEqual(venda.uf_destino, "SP")