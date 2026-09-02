from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


ENV_DIRETORIO_SECRETS_A1 = "PROCASH_SECRETS_A1_DIR"
ENV_CHAVE_MESTRA_SECRETS_A1 = "PROCASH_SECRETS_A1_MASTER_KEY"


class SegredoCertificadoA1Error(ValueError):
    """Falha segura ao armazenar ou resolver a senha do certificado A1."""


def _diretorio_privado_secrets_a1() -> Path:
    valor = str(os.environ.get(ENV_DIRETORIO_SECRETS_A1, "") or "").strip()
    if not valor:
        raise SegredoCertificadoA1Error(
            "Diretorio privado de secrets A1 nao configurado."
        )
    try:
        return Path(valor).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise SegredoCertificadoA1Error(
            "Diretorio privado de secrets A1 invalido."
        ) from exc


def _fernet() -> Fernet:
    valor = str(os.environ.get(ENV_CHAVE_MESTRA_SECRETS_A1, "") or "").strip()
    if not valor:
        raise SegredoCertificadoA1Error(
            "Chave-mestra de secrets A1 nao configurada."
        )
    try:
        return Fernet(valor.encode("ascii"))
    except (UnicodeEncodeError, ValueError) as exc:
        raise SegredoCertificadoA1Error(
            "Chave-mestra de secrets A1 invalida."
        ) from exc


def _resolver_caminho_privado(referencia: str) -> tuple[Path, Path]:
    base = _diretorio_privado_secrets_a1()
    valor = str(referencia or "").strip()
    if not valor:
        raise SegredoCertificadoA1Error("Referencia de secret A1 ausente.")
    try:
        alvo = Path(valor).expanduser().resolve()
        alvo.relative_to(base)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SegredoCertificadoA1Error("Referencia de secret A1 invalida.") from exc
    return base, alvo


def _nome_opaco(*, loja_id) -> str:
    identificador_loja = str(loja_id)
    for _ in range(100):
        candidato = f"secret-{uuid.uuid4().hex}.bin"
        if identificador_loja not in candidato:
            return candidato
    raise SegredoCertificadoA1Error("Nao foi possivel gerar referencia segura.")


def armazenar_senha_certificado_a1(*, loja_id, senha: str) -> str:
    if not isinstance(senha, str) or not senha:
        raise SegredoCertificadoA1Error("Senha do certificado A1 ausente.")

    base = _diretorio_privado_secrets_a1()
    cifra = _fernet()
    try:
        base.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(base, 0o700)
        except OSError:
            pass
        destino = base / _nome_opaco(loja_id=loja_id)
        conteudo = cifra.encrypt(senha.encode("utf-8"))
        descritor, temporario_texto = tempfile.mkstemp(
            prefix=".secret-a1-",
            suffix=".tmp",
            dir=str(base),
        )
        temporario = Path(temporario_texto)
        try:
            with os.fdopen(descritor, "wb") as arquivo:
                arquivo.write(conteudo)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            try:
                os.chmod(temporario, 0o600)
            except OSError:
                pass
            os.replace(temporario, destino)
            try:
                os.chmod(destino, 0o600)
            except OSError:
                pass
        finally:
            if temporario.exists():
                temporario.unlink()
    except SegredoCertificadoA1Error:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise SegredoCertificadoA1Error(
            "Nao foi possivel armazenar o secret A1."
        ) from exc
    return str(destino)


def resolver_senha_certificado_a1(referencia: str) -> str:
    _, alvo = _resolver_caminho_privado(referencia)
    cifra = _fernet()
    try:
        conteudo = alvo.read_bytes()
        senha = cifra.decrypt(conteudo).decode("utf-8")
    except (OSError, InvalidToken, UnicodeError, ValueError) as exc:
        raise SegredoCertificadoA1Error(
            "Nao foi possivel resolver o secret A1."
        ) from exc
    if not senha:
        raise SegredoCertificadoA1Error("Secret A1 vazio.")
    return senha


def remover_senha_certificado_a1(referencia: str) -> None:
    _, alvo = _resolver_caminho_privado(referencia)
    try:
        alvo.unlink(missing_ok=True)
    except OSError as exc:
        raise SegredoCertificadoA1Error(
            "Nao foi possivel remover o secret A1."
        ) from exc
