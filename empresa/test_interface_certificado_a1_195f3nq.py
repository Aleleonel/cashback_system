from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path
from django.test import SimpleTestCase
from empresa.forms import ConfiguracaoFiscalLojaEmpresaForm
class InterfaceA1Tests(SimpleTestCase):
    def test_campos_seguros(self):
        self.assertIn('certificado_a1_arquivo',ConfiguracaoFiscalLojaEmpresaForm.base_fields); self.assertIn('certificado_a1_senha',ConfiguracaoFiscalLojaEmpresaForm.base_fields); self.assertNotIn('certificado_a1_referencia',ConfiguracaoFiscalLojaEmpresaForm.base_fields)
    def test_multipart(self):
        t=(Path(__file__).resolve().parent/'templates'/'empresa'/'form_loja.html').read_text(encoding='utf-8'); self.assertIn('enctype="multipart/form-data"',t); self.assertIn('fiscal_form.certificado_a1_arquivo',t)

class HardeningInterfaceCertificadoA1Tests(SimpleTestCase):
    def _arquivo(self):
        return SimpleUploadedFile(
            'certificado.pfx',
            b'conteudo-sintetico-nao-certificado',
            content_type='application/x-pkcs12',
        )

    def test_arquivo_sem_senha_e_invalido(self):
        form = ConfiguracaoFiscalLojaEmpresaForm(
            data={},
            files={'certificado_a1_arquivo': self._arquivo()},
        )
        form.is_valid()
        self.assertIn('certificado_a1_senha', form.errors)

    def test_senha_sem_arquivo_e_invalida(self):
        form = ConfiguracaoFiscalLojaEmpresaForm(
            data={'certificado_a1_senha': 'senha-sintetica'},
        )
        form.is_valid()
        self.assertIn('certificado_a1_arquivo', form.errors)

    def test_sem_upload_nao_cria_erro_a1(self):
        form = ConfiguracaoFiscalLojaEmpresaForm(data={})
        form.is_valid()
        self.assertNotIn('certificado_a1_arquivo', form.errors)
        self.assertNotIn('certificado_a1_senha', form.errors)
