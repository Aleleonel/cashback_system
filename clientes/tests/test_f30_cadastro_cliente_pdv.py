from pathlib import Path
from django.test import SimpleTestCase
ROOT = Path(__file__).resolve().parents[2]
class F30CadastroClientePdvContractTest(SimpleTestCase):
    def test_operador_pdv_pode_criar_cliente(self):
        s=(ROOT/"accounts"/"permissions.py").read_text(encoding="utf-8")
        i=s.index("PERMISSOES_PDV_OPERADOR")
        self.assertIn("PERMISSAO_CLIENTES_CRIAR",s[i:i+900])
    def test_pdv_oferece_acao_cadastrar_cliente(self):
        s=(ROOT/"pdv"/"templates"/"pdv"/"inicio.html").read_text(encoding="utf-8")
        self.assertIn("clientes:criar_cliente",s);self.assertIn("origem=pdv",s)
    def test_criar_cliente_reconhece_retorno_ao_pdv(self):
        s=(ROOT/"clientes"/"views.py").read_text(encoding="utf-8")
        self.assertIn("origem_pdv",s);self.assertIn("pdv:inicio",s);self.assertIn("cliente.id",s)
    def test_estado_pdv_ja_e_persistido(self):
        s=(ROOT/"pdv"/"static"/"pdv"/"js"/"frente_caixa.js").read_text(encoding="utf-8")
        self.assertIn("carregarEstado",s);self.assertIn("selecionarClienteUrl",s)
    def test_retorno_pdv_filtra_venda_por_operador(self):
        fonte = (ROOT/"clientes"/"views.py").read_text(encoding="utf-8")
        inicio = fonte.index("if origem_pdv:")
        trecho = fonte[inicio:]

        self.assertIn("operador_abertura=request.user", trecho)
        self.assertIn("status=StatusSessaoCaixa.ABERTA", trecho)
        self.assertIn("sessao_caixa=sessao", trecho)
        self.assertIn("operador=request.user", trecho)
        self.assertNotIn("sessao_caixa__operador=request.user", trecho)

    def test_busca_cliente_alfanumerica_nao_amplia_por_digitos(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        views = (root / "pdv" / "views.py").read_text(encoding="utf-8-sig")
        self.assertIn(
            "termo_tem_letras = any(caractere.isalpha() for caractere in termo)",
            views,
        )
        self.assertIn(
            "if somente_numeros and not termo_tem_letras:",
            views,
        )

    def test_pdv_nao_duplica_renderizacao_global_de_messages(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        pdv = (root / "pdv/templates/pdv/inicio.html").read_text(encoding="utf-8-sig")
        base = (root / "templates/base.html").read_text(encoding="utf-8-sig")
        self.assertNotIn("for message in messages", pdv)
        self.assertIn("for message in messages", base)
