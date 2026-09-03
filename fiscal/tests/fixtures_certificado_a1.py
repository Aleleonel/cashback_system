import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


def criar_pkcs12_sintetico(
    pasta,
    *,
    senha,
    nome_comum="A1 SINTETICO TESTE",
    nome_arquivo="certificado-sintetico.pfx",
):
    """Cria PKCS#12 efemero exclusivamente para testes locais."""
    pasta = Path(pasta)
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nome_comum)])
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
        name=b"a1-sintetico",
        key=chave,
        cert=certificado,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(
            str(senha).encode("utf-8")
        ),
    )
    caminho = pasta / nome_arquivo
    caminho.write_bytes(blob)
    return caminho
