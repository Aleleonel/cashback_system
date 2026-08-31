from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from empresas.models import Loja, Matriz
from core.choices import StatusOperacional
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_certificado_a1 import CertificadoA1Error


class TransacaoCertificadoA1PostTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz NT8")
        self.loja_contexto = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Contexto NT8",
            status=StatusOperacional.ATIVA,
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="master_nt8",
            password="123456",
            matriz=self.matriz,
            perfil=User.PERFIL_MASTER,
        )
        self.usuario.lojas.add(self.loja_contexto)
        self.client.force_login(self.usuario)

    def fiscal_payload(self):
        return {
            "configurar_fiscal": "1",
            "razao_social": "Empresa NT8 Ltda",
            "nome_fantasia": "Empresa NT8",
            "inscricao_estadual": "123456789",
            "logradouro": "Rua Teste",
            "numero": "100",
            "complemento": "",
            "bairro": "Centro",
            "municipio": "Sao Paulo",
            "codigo_municipio_ibge": "3550308",
            "uf": "SP",
            "cep": "01001000",
            "crt": "3",
            "ambiente_nfce": "homologacao",
            "serie_nfce": "1",
            "ativa": "on",
        }

    def upload(self):
        return SimpleUploadedFile(
            "certificado.pfx",
            b"PKCS12-SINTETICO-NT8",
            content_type="application/x-pkcs12",
        )

    @patch("empresa.views.lojas.armazenar_certificado_a1")
    def test_criacao_falha_a1_reverte_loja_e_configuracao_fiscal(self, armazenar):
        armazenar.side_effect = CertificadoA1Error(
            "Nao foi possivel carregar o certificado A1. Verifique arquivo e senha."
        )
        dados = self.fiscal_payload()
        dados.update({
            "nome": "Loja Criacao Rollback NT8",
            "cnpj": "12345678000195",
            "telefone": "11999999999",
            "status": StatusOperacional.ATIVA,
            "certificado_a1_arquivo": self.upload(),
            "certificado_a1_senha": "senha-errada-nt8",
        })

        resposta = self.client.post(reverse("empresa:criar_loja"), data=dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(
            Loja.objects.filter(
                matriz=self.matriz,
                nome="Loja Criacao Rollback NT8",
            ).exists()
        )
        self.assertFalse(
            ConfiguracaoEmissaoFiscalLoja.objects.filter(
                loja__matriz=self.matriz,
                loja__nome="Loja Criacao Rollback NT8",
            ).exists()
        )
        self.assertContains(resposta, "Nao foi possivel carregar o certificado A1")

    @patch("empresa.views.lojas.armazenar_certificado_a1")
    def test_edicao_falha_a1_reverte_alteracoes_da_loja_e_fiscal(self, armazenar):
        loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Antes NT8",
            cnpj="22345678000190",
            telefone="11111111111",
            status=StatusOperacional.ATIVA,
        )
        cfg = ConfiguracaoEmissaoFiscalLoja.objects.create(
            loja=loja,
            razao_social="Razao Antes NT8",
            nome_fantasia="Fantasia Antes",
            inscricao_estadual="123456789",
            logradouro="Rua Antes",
            numero="1",
            complemento="",
            bairro="Centro",
            municipio="Sao Paulo",
            codigo_municipio_ibge="3550308",
            uf="SP",
            cep="01001000",
            crt="3",
            ambiente_nfce="homologacao",
            serie_nfce=1,
            ativa=True,
        )
        armazenar.side_effect = CertificadoA1Error(
            "Nao foi possivel carregar o certificado A1. Verifique arquivo e senha."
        )
        dados = self.fiscal_payload()
        dados.update({
            "nome": "Loja Depois NT8",
            "cnpj": "22345678000190",
            "telefone": "11988888888",
            "status": StatusOperacional.SUSPENSA,
            "razao_social": "Razao Depois NT8",
            "certificado_a1_arquivo": self.upload(),
            "certificado_a1_senha": "senha-errada-nt8",
        })

        resposta = self.client.post(
            reverse("empresa:editar_loja", args=[loja.pk]),
            data=dados,
        )

        self.assertEqual(resposta.status_code, 200)
        loja.refresh_from_db()
        cfg.refresh_from_db()
        self.assertEqual(loja.nome, "Loja Antes NT8")
        self.assertEqual(loja.telefone, "11111111111")
        self.assertEqual(loja.status, StatusOperacional.ATIVA)
        self.assertEqual(cfg.razao_social, "Razao Antes NT8")
        self.assertContains(resposta, "Nao foi possivel carregar o certificado A1")

    @patch("empresa.views.lojas.armazenar_certificado_a1")
    def test_edicao_sem_upload_preserva_referencia_a1(self, armazenar):
        loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Preserva NT8",
            cnpj="32345678000194",
            status=StatusOperacional.ATIVA,
        )
        cfg = ConfiguracaoEmissaoFiscalLoja.objects.create(
            loja=loja,
            razao_social="Razao Preserva NT8",
            nome_fantasia="Preserva",
            inscricao_estadual="123456789",
            logradouro="Rua Preserva",
            numero="10",
            complemento="",
            bairro="Centro",
            municipio="Sao Paulo",
            codigo_municipio_ibge="3550308",
            uf="SP",
            cep="01001000",
            crt="3",
            ambiente_nfce="homologacao",
            serie_nfce=1,
            ativa=True,
            certificado_a1_referencia="C:/privado/existente.pfx",
        )
        dados = self.fiscal_payload()
        dados.update({
            "nome": "Loja Preserva Editada NT8",
            "cnpj": "32345678000194",
            "telefone": "",
            "status": StatusOperacional.ATIVA,
            "razao_social": "Razao Preserva Editada NT8",
        })

        resposta = self.client.post(
            reverse("empresa:editar_loja", args=[loja.pk]),
            data=dados,
        )

        self.assertEqual(resposta.status_code, 302)
        cfg.refresh_from_db()
        self.assertEqual(
            cfg.certificado_a1_referencia,
            "C:/privado/existente.pfx",
        )
        armazenar.assert_not_called()