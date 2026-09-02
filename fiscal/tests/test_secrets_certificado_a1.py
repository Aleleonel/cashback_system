import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cryptography.fernet import Fernet

from fiscal.services_secrets_certificado_a1 import (
    SegredoCertificadoA1Error,
    armazenar_senha_certificado_a1,
    remover_senha_certificado_a1,
    resolver_senha_certificado_a1,
)


class SecretsCertificadoA1ContractTests(TestCase):
    ENV_DIR = "PROCASH_SECRETS_A1_DIR"
    ENV_KEY = "PROCASH_SECRETS_A1_MASTER_KEY"
    SENHA_FICTICIA = "senha-a1-ficticia-195f3nx"

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.master_key = Fernet.generate_key().decode("ascii")
        self.env = {
            self.ENV_DIR: self.temp_dir.name,
            self.ENV_KEY: self.master_key,
        }

    def _armazenar(self):
        with patch.dict(os.environ, self.env, clear=False):
            return armazenar_senha_certificado_a1(
                loja_id=195,
                senha=self.SENHA_FICTICIA,
            )

    def test_round_trip_retorna_senha_ficticia(self):
        referencia = self._armazenar()
        with patch.dict(os.environ, self.env, clear=False):
            resolvida = resolver_senha_certificado_a1(referencia)
        self.assertEqual(resolvida, self.SENHA_FICTICIA)

    def test_arquivo_criptografado_nao_contem_senha_em_texto_puro(self):
        referencia = self._armazenar()
        conteudo = Path(referencia).read_bytes()
        self.assertNotIn(self.SENHA_FICTICIA.encode("utf-8"), conteudo)

    def test_referencia_e_opaca_e_nao_expoe_loja(self):
        referencia = self._armazenar()
        nome = Path(referencia).name
        self.assertNotIn("195", nome)
        self.assertNotIn(self.SENHA_FICTICIA, referencia)

    def test_chave_mestra_errada_nao_descriptografa(self):
        referencia = self._armazenar()
        env_errado = dict(self.env)
        env_errado[self.ENV_KEY] = Fernet.generate_key().decode("ascii")
        with patch.dict(os.environ, env_errado, clear=False):
            with self.assertRaises(SegredoCertificadoA1Error) as ctx:
                resolver_senha_certificado_a1(referencia)
        self.assertNotIn(self.SENHA_FICTICIA, str(ctx.exception))

    def test_segredo_adulterado_nao_descriptografa(self):
        referencia = self._armazenar()
        caminho = Path(referencia)
        conteudo = bytearray(caminho.read_bytes())
        conteudo[-1] ^= 1
        caminho.write_bytes(bytes(conteudo))
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaises(SegredoCertificadoA1Error) as ctx:
                resolver_senha_certificado_a1(referencia)
        self.assertNotIn(self.SENHA_FICTICIA, str(ctx.exception))

    def test_chave_mestra_ausente_falha_sem_expor_senha(self):
        env_sem_chave = dict(self.env)
        env_sem_chave.pop(self.ENV_KEY)
        with patch.dict(os.environ, env_sem_chave, clear=True):
            with self.assertRaises(SegredoCertificadoA1Error) as ctx:
                armazenar_senha_certificado_a1(
                    loja_id=195,
                    senha=self.SENHA_FICTICIA,
                )
        self.assertNotIn(self.SENHA_FICTICIA, str(ctx.exception))

    def test_referencia_fora_do_diretorio_privado_e_rejeitada(self):
        with tempfile.NamedTemporaryFile() as externo:
            with patch.dict(os.environ, self.env, clear=False):
                with self.assertRaises(SegredoCertificadoA1Error):
                    resolver_senha_certificado_a1(externo.name)

    def test_remocao_e_idempotente(self):
        referencia = self._armazenar()
        with patch.dict(os.environ, self.env, clear=False):
            remover_senha_certificado_a1(referencia)
            remover_senha_certificado_a1(referencia)
        self.assertFalse(Path(referencia).exists())

    def test_senha_vazia_e_rejeitada(self):
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaises(SegredoCertificadoA1Error):
                armazenar_senha_certificado_a1(loja_id=195, senha="")
