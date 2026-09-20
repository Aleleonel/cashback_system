from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Loja, Matriz
from pdv.choices import TipoMovimentacaoCaixa
from pdv.models import Caixa, MovimentacaoCaixa, SessaoCaixa
from pdv.services.vendas.caixa import registrar_movimentacao_caixa_operacional


class R9KUX16SaldoCaixaRedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.matriz = Matriz.objects.create(nome="Matriz R9KUX16")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R9KUX16")
        self.user = User.objects.create_user(
            username="r9kux16", password="x", matriz=self.matriz
        )
        self.user.lojas.add(self.loja)
        self.caixa = Caixa.objects.create(
            matriz=self.matriz, loja=self.loja,
            codigo="CX16", nome="Caixa R9KUX16",
        )
        self.sessao = SessaoCaixa.objects.create(
            caixa=self.caixa,
            operador_abertura=self.user,
            valor_abertura=Decimal("0.00"),
        )

    def test_sangria_maior_que_saldo_deve_ser_rejeitada_sem_movimento(self):
        registrar_movimentacao_caixa_operacional(
            sessao_caixa=self.sessao,
            tipo=TipoMovimentacaoCaixa.SUPRIMENTO,
            valor=Decimal("15.00"),
            operador=self.user,
            descricao="Suprimento teste",
        )
        antes = MovimentacaoCaixa.objects.filter(
            sessao_caixa=self.sessao
        ).count()

        with self.assertRaises(ValidationError):
            registrar_movimentacao_caixa_operacional(
                sessao_caixa=self.sessao,
                tipo=TipoMovimentacaoCaixa.SANGRIA,
                valor=Decimal("15.01"),
                operador=self.user,
                descricao="Nao pode negativar",
            )

        self.assertEqual(
            MovimentacaoCaixa.objects.filter(
                sessao_caixa=self.sessao
            ).count(),
            antes,
        )

    def test_sangria_exatamente_igual_ao_saldo_deve_ser_permitida(self):
        registrar_movimentacao_caixa_operacional(
            sessao_caixa=self.sessao,
            tipo=TipoMovimentacaoCaixa.SUPRIMENTO,
            valor=Decimal("15.00"),
            operador=self.user,
            descricao="Suprimento teste",
        )
        mov = registrar_movimentacao_caixa_operacional(
            sessao_caixa=self.sessao,
            tipo=TipoMovimentacaoCaixa.SANGRIA,
            valor=Decimal("15.00"),
            operador=self.user,
            descricao="Sangria total",
        )
        self.assertEqual(mov.tipo, TipoMovimentacaoCaixa.SANGRIA)
        self.assertEqual(mov.valor, Decimal("15.00"))


class R9KUX16UiContratoRedTests(TestCase):
    def test_rotas_operacionais_de_suprimento_e_sangria_devem_existir(self):
        texto = Path("pdv/urls.py").read_text(encoding="utf-8")
        self.assertIn('name="suprimento_caixa"', texto)
        self.assertIn('name="sangria_caixa"', texto)

    def test_ui_deve_usar_servico_operacional_e_permissoes_formais(self):
        texto = Path("pdv/views.py").read_text(encoding="utf-8")
        self.assertIn("registrar_movimentacao_caixa_operacional", texto)
        self.assertIn("PERMISSAO_PDV_SUPRIMENTO", texto)
        self.assertIn("PERMISSAO_PDV_SANGRIA", texto)