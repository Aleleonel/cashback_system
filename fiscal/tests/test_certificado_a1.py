import datetime
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase

from fiscal.services_certificado_a1 import CertificadoA1Error, carregar_certificado_a1
from fiscal.tests.fixtures_certificado_a1 import criar_pkcs12_sintetico


class CarregadorCertificadoA1Tests(SimpleTestCase):
    SENHA = "senha-teste-195f3k"

    def _criar_pkcs12(self, pasta: str) -> Path:
        return criar_pkcs12_sintetico(
            pasta,
            senha=self.SENHA,
        )

    def test_carrega_pkcs12_com_chave_rsa_e_certificado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = self._criar_pkcs12(pasta)
            resultado = carregar_certificado_a1(
                referencia=str(caminho),
                senha=self.SENHA,
            )
            self.assertIsInstance(resultado.chave_privada, rsa.RSAPrivateKey)
            self.assertIsNotNone(resultado.certificado)

    def test_rejeita_referencia_vazia(self):
        with self.assertRaisesRegex(CertificadoA1Error, "Referencia"):
            carregar_certificado_a1(referencia="", senha=self.SENHA)

    def test_rejeita_arquivo_inexistente(self):
        with self.assertRaisesRegex(CertificadoA1Error, "nao encontrado"):
            carregar_certificado_a1(
                referencia="arquivo-que-nao-existe-195f3k.pfx",
                senha=self.SENHA,
            )

    def test_rejeita_senha_invalida_sem_expor_segredo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = self._criar_pkcs12(pasta)
            senha_errada = "SEGREDO-NAO-PODE-APARECER"
            with self.assertRaises(CertificadoA1Error) as ctx:
                carregar_certificado_a1(
                    referencia=str(caminho),
                    senha=senha_errada,
                )
            self.assertNotIn(senha_errada, str(ctx.exception))