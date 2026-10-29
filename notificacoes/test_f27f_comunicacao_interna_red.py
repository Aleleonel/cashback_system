from django.test import TestCase
from django.urls import reverse
from notificacoes import models as notificacoes_models
from configuracoes import catalogo


def localizar_card(codigo):
    """Localiza o card no catalogo real sem presumir o nome da colecao."""
    visitados = set()

    def caminhar(obj):
        oid = id(obj)
        if oid in visitados:
            return None
        visitados.add(oid)

        if getattr(obj, "codigo", None) == codigo:
            return obj

        if isinstance(obj, dict):
            valores = obj.values()
        elif isinstance(obj, (list, tuple, set)):
            valores = obj
        else:
            return None

        for valor in valores:
            achado = caminhar(valor)
            if achado is not None:
                return achado
        return None

    for nome, valor in vars(catalogo).items():
        if nome.startswith("__"):
            continue
        achado = caminhar(valor)
        if achado is not None:
            return achado
    return None


class F27FComunicacaoInternaRedTests(TestCase):
    def test_modelo_aviso_interno_existe(self):
        self.assertTrue(hasattr(notificacoes_models, "AvisoInterno"))

    def test_modelo_leitura_aviso_existe(self):
        self.assertTrue(hasattr(notificacoes_models, "LeituraAviso"))

    def test_aviso_possui_contrato_minimo(self):
        model = getattr(notificacoes_models, "AvisoInterno")
        nomes = {f.name for f in model._meta.get_fields()}
        esperados = {
            "matriz", "loja", "titulo", "mensagem", "prioridade",
            "inicio_exibicao", "fim_exibicao", "ativo", "criado_por",
        }
        self.assertTrue(esperados.issubset(nomes), esperados - nomes)

    def test_leitura_vincula_aviso_usuario_e_data(self):
        model = getattr(notificacoes_models, "LeituraAviso")
        nomes = {f.name for f in model._meta.get_fields()}
        self.assertTrue({"aviso", "usuario", "lido_em"}.issubset(nomes))

    def test_rota_administrativa_central_existe(self):
        self.assertEqual(
            reverse("configuracoes:notificacoes"),
            "/configuracoes/notificacoes/",
        )

    def test_rota_usuario_notificacoes_existe(self):
        self.assertEqual(reverse("notificacoes:lista"), "/notificacoes/")

    def test_rota_marcar_como_lida_existe(self):
        reverse("notificacoes:marcar_lida", kwargs={"pk": 1})

    def test_card_hub_notificacoes_fica_disponivel(self):
        card = localizar_card("notificacoes")
        self.assertIsNotNone(card, "Card notificacoes nao localizado no catalogo real")
        self.assertTrue(card.disponivel)
        self.assertEqual(card.url_name, "configuracoes:notificacoes")
