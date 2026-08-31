import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from fiscal.services_armazenamento_certificado_a1 import armazenar_certificado_a1,remover_certificado_a1_por_referencia
class ArmazenamentoA1Tests(SimpleTestCase):
    def test_rejeita_extensao(self):
        with self.assertRaises(ValidationError): armazenar_certificado_a1(loja_id=1,arquivo=SimpleUploadedFile('x.txt',b'x'),senha='s')
    @patch('fiscal.services_armazenamento_certificado_a1.carregar_certificado_a1')
    def test_valida_grava_remove(self,loader):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict('os.environ',{'PROCASH_CERTIFICADOS_A1_DIR':d}):
                r=armazenar_certificado_a1(loja_id=7,arquivo=SimpleUploadedFile('x.pfx',b'abc'),senha='segredo')
                self.assertEqual(Path(r).read_bytes(),b'abc'); loader.assert_called_once(); self.assertNotIn('segredo',r)
                remover_certificado_a1_por_referencia(r); self.assertFalse(Path(r).exists())
