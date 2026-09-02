from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from empresa.views.lojas import UploadA1Persistido, _persistir_upload_a1_se_informado
from fiscal.services_secrets_certificado_a1 import SegredoCertificadoA1Error


class TransacaoUploadSecretsA1ContractTests(SimpleTestCase):
    def _form(self, *, arquivo=object(), senha="senha-ficticia-195f3nzd"):
        return SimpleNamespace(
            cleaned_data={
                "certificado_a1_arquivo": arquivo,
                "certificado_a1_senha": senha,
            }
        )

    def _configuracao(self):
        cfg = Mock()
        cfg.certificado_a1_referencia = "a1-antigo.pfx"
        cfg.certificado_a1_segredo_referencia = "secret-antigo.bin"
        return cfg

    @patch("empresa.views.lojas.transaction.on_commit")
    @patch("empresa.views.lojas.remover_senha_certificado_a1")
    @patch("empresa.views.lojas.remover_certificado_a1_por_referencia")
    @patch("empresa.views.lojas.armazenar_senha_certificado_a1")
    @patch("empresa.views.lojas.armazenar_certificado_a1")
    @patch("empresa.views.lojas.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_sucesso_persiste_duas_referencias_e_remove_antigas_pos_commit(
        self,
        get_configuracao,
        armazenar_certificado,
        armazenar_senha,
        remover_certificado,
        remover_senha,
        on_commit,
    ):
        cfg = self._configuracao()
        get_configuracao.return_value = cfg
        armazenar_certificado.return_value = "a1-novo.pfx"
        armazenar_senha.return_value = "secret-novo.bin"

        resultado = _persistir_upload_a1_se_informado(
            loja=SimpleNamespace(pk=195),
            fiscal_form=self._form(),
        )

        self.assertEqual(
            resultado,
            UploadA1Persistido("a1-novo.pfx", "secret-novo.bin"),
        )
        self.assertEqual(cfg.certificado_a1_referencia, "a1-novo.pfx")
        self.assertEqual(
            cfg.certificado_a1_segredo_referencia,
            "secret-novo.bin",
        )
        cfg.full_clean.assert_called_once_with()
        cfg.save.assert_called_once()
        self.assertEqual(on_commit.call_count, 2)

        for chamada in on_commit.call_args_list:
            chamada.args[0]()

        remover_certificado.assert_called_once_with("a1-antigo.pfx")
        remover_senha.assert_called_once_with("secret-antigo.bin")

    @patch("empresa.views.lojas.remover_senha_certificado_a1")
    @patch("empresa.views.lojas.remover_certificado_a1_por_referencia")
    @patch("empresa.views.lojas.armazenar_senha_certificado_a1")
    @patch("empresa.views.lojas.armazenar_certificado_a1")
    @patch("empresa.views.lojas.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_falha_ao_armazenar_secret_remove_novo_certificado(
        self,
        get_configuracao,
        armazenar_certificado,
        armazenar_senha,
        remover_certificado,
        remover_senha,
    ):
        cfg = self._configuracao()
        get_configuracao.return_value = cfg
        armazenar_certificado.return_value = "a1-novo.pfx"
        armazenar_senha.side_effect = SegredoCertificadoA1Error("falha segura")

        with self.assertRaises(SegredoCertificadoA1Error):
            _persistir_upload_a1_se_informado(
                loja=SimpleNamespace(pk=195),
                fiscal_form=self._form(),
            )

        remover_certificado.assert_called_once_with("a1-novo.pfx")
        remover_senha.assert_not_called()
        self.assertEqual(cfg.certificado_a1_referencia, "a1-antigo.pfx")
        self.assertEqual(
            cfg.certificado_a1_segredo_referencia,
            "secret-antigo.bin",
        )

    @patch("empresa.views.lojas.remover_senha_certificado_a1")
    @patch("empresa.views.lojas.remover_certificado_a1_por_referencia")
    @patch("empresa.views.lojas.armazenar_senha_certificado_a1")
    @patch("empresa.views.lojas.armazenar_certificado_a1")
    @patch("empresa.views.lojas.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_falha_ao_salvar_remove_novo_certificado_e_novo_secret(
        self,
        get_configuracao,
        armazenar_certificado,
        armazenar_senha,
        remover_certificado,
        remover_senha,
    ):
        cfg = self._configuracao()
        cfg.save.side_effect = RuntimeError("falha simulada")
        get_configuracao.return_value = cfg
        armazenar_certificado.return_value = "a1-novo.pfx"
        armazenar_senha.return_value = "secret-novo.bin"

        with self.assertRaises(RuntimeError):
            _persistir_upload_a1_se_informado(
                loja=SimpleNamespace(pk=195),
                fiscal_form=self._form(),
            )

        remover_certificado.assert_called_once_with("a1-novo.pfx")
        remover_senha.assert_called_once_with("secret-novo.bin")

    @patch("empresa.views.lojas.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_sem_upload_retorna_referencias_vazias_e_nao_altera_configuracao(
        self,
        get_configuracao,
    ):
        resultado = _persistir_upload_a1_se_informado(
            loja=SimpleNamespace(pk=195),
            fiscal_form=self._form(arquivo=None, senha=""),
        )

        self.assertEqual(resultado, UploadA1Persistido(None, None))
        get_configuracao.assert_not_called()
