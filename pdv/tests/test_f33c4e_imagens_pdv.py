"""F33C4E: testes focais para imagens de produtos e pesquisa PDV."""
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from produtos.forms import ProdutoForm
from pdv.tests.test_frente_caixa_web import FrenteCaixaWebTests


def imagem(nome="produto.png", formato="PNG"):
    memoria = BytesIO()
    Image.new("RGB", (2, 2), (100, 120, 140)).save(memoria, format=formato)
    return SimpleUploadedFile(nome, memoria.getvalue(), content_type="image/png")


class F33C4EImagemPDVTests(FrenteCaixaWebTests):
    """Reutiliza o contexto operacional real do PDV já coberto pela suíte."""

    def test_f33c4e_pdv_sem_imagem_retorna_null(self):
        from django.urls import reverse
        resposta = self.client.get(reverse("pdv:buscar_produtos"), {"q": "Frente"})
        self.assertEqual(resposta.status_code, 200)
        item = next(p for p in resposta.json()["produtos"] if p["id"] == self.produto.pk)
        self.assertIsNone(item["imagem_url"])

    def test_f33c4e_pdv_com_imagem_retorna_url(self):
        from django.urls import reverse
        with TemporaryDirectory() as pasta, override_settings(MEDIA_ROOT=pasta, MEDIA_URL="/media/"):
            self.produto.imagem_principal = imagem()
            self.produto.save(update_fields=["imagem_principal"])
            resposta = self.client.get(reverse("pdv:buscar_produtos"), {"q": "Frente"})
            self.assertEqual(resposta.status_code, 200)
            item = next(p for p in resposta.json()["produtos"] if p["id"] == self.produto.pk)
            self.assertTrue(item["imagem_url"].startswith("/media/produtos/matriz_"))
            self.assertTrue(item["imagem_url"].endswith(".png"))

    def test_f33c4e_formulario_rejeita_extensao_invalida(self):
        form = ProdutoForm(matriz=self.matriz)
        self.assertIn("imagem_principal", form.fields)
        arquivo = SimpleUploadedFile("produto.txt", b"nao e imagem", content_type="text/plain")
        campo = form.fields["imagem_principal"]
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            campo.clean(arquivo)

    def test_f33c4e_formulario_rejeita_arquivo_maior_que_3mb(self):
        from django.core.exceptions import ValidationError
        form = ProdutoForm(matriz=self.matriz)
        form.cleaned_data = {"imagem_principal": SimpleUploadedFile("produto.png", b"a" * (3 * 1024 * 1024 + 1), content_type="image/png")}
        with self.assertRaises(ValidationError):
            form.clean_imagem_principal()
