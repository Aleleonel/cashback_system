from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12


class CertificadoA1Error(ValueError):
    """Falha controlada ao localizar ou carregar um certificado digital A1."""


@dataclass(frozen=True)
class CertificadoA1:
    chave_privada: rsa.RSAPrivateKey
    certificado: object
    certificados_adicionais: tuple


def carregar_certificado_a1(*, referencia: str, senha: str) -> CertificadoA1:
    """Carrega um PKCS#12 A1 sem persistir senha ou material criptografico."""
    ref = str(referencia or "").strip()
    if not ref:
        raise CertificadoA1Error("Referencia do certificado A1 nao informada.")

    caminho = Path(ref).expanduser()
    if not caminho.is_file():
        raise CertificadoA1Error("Certificado A1 nao encontrado na referencia informada.")

    if senha is None or not isinstance(senha, str):
        raise CertificadoA1Error("Senha do certificado A1 nao informada.")

    try:
        conteudo = caminho.read_bytes()
        chave, certificado, adicionais = pkcs12.load_key_and_certificates(
            conteudo,
            senha.encode("utf-8"),
        )
    except Exception as exc:
        raise CertificadoA1Error(
            "Nao foi possivel carregar o certificado A1. Verifique arquivo e senha."
        ) from exc

    if chave is None or certificado is None:
        raise CertificadoA1Error("PKCS#12 nao contem chave privada e certificado.")

    if not isinstance(chave, rsa.RSAPrivateKey):
        raise CertificadoA1Error("A chave privada do certificado A1 deve ser RSA.")

    return CertificadoA1(
        chave_privada=chave,
        certificado=certificado,
        certificados_adicionais=tuple(adicionais or ()),
    )