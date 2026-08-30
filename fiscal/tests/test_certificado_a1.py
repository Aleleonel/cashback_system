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


class CarregadorCertificadoA1Tests(SimpleTestCase):
    SENHA = "senha-teste-195f3k"

    def _criar_pkcs12(self, pasta: str) -> Path:
        chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "195F3K Teste A1")])
        agora = datetime.datetime.now(datetime.timezone.utc)
        certificado = (
            x509.CertificateBuilder()
            .subject_name(nome)
            .issuer_name(nome)
            .public_key(chave.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(agora - datetime.timedelta(minutes=1))
            .not_valid_after(agora + datetime.timedelta(days=1))
            .sign(chave, hashes.SHA256())
        )
        blob = pkcs12.serialize_key_and_certificates(
            name=b"195F3K",
            key=chave,
            cert=certificado,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(
                self.SENHA.encode("utf-8")
            ),
        )
        caminho = Path(pasta) / "certificado_teste_195f3k.pfx"
        caminho.write_bytes(blob)
        return caminho

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