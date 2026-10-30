from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from cashback.models import LancamentoCashback

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from vouchers.forms import VoucherForm
from vouchers.models import ComissaoParceiro, Parceiro, UsoVoucher, Voucher, VoucherLoja


class VoucherModelTest(TestCase):

    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Teste'
        )

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Teste',
            cpf='12345678900'
        )

        self.User = get_user_model()

        self.usuario = self.User.objects.create_user(
            username='usuario_voucher',
            password='123456',
            matriz=self.matriz
        )

        self.usuario.lojas.add(self.loja)

    def test_voucher_valor_fixo_disponivel_para_uso(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE1',
            nome='Voucher Teste',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=5
        )

        self.assertTrue(voucher.disponivel_para_uso)

    def test_voucher_expirado_nao_disponivel(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE2',
            nome='Voucher Expirado',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje - timedelta(days=10),
            data_fim=hoje - timedelta(days=1),
            limite_utilizacao=5
        )

        self.assertTrue(voucher.esta_expirado)
        self.assertFalse(voucher.disponivel_para_uso)

    def test_voucher_esgotado_nao_disponivel(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE3',
            nome='Voucher Esgotado',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=1,
            total_utilizado=1
        )

        self.assertTrue(voucher.esta_esgotado)
        self.assertFalse(voucher.disponivel_para_uso)

    def test_voucher_loja_relacionamento(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE4',
            nome='Voucher Loja',
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=3
        )

        relacao = VoucherLoja.objects.create(
            voucher=voucher,
            loja=self.loja
        )

        self.assertEqual(relacao.voucher, voucher)
        self.assertEqual(relacao.loja, self.loja)

    def test_uso_voucher(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE5',
            nome='Voucher Uso',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('15.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=2
        )

        uso = UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=voucher,
            cliente=self.cliente,
            loja=self.loja,
            usuario=self.usuario,
            valor_compra=Decimal('100.00'),
            valor_desconto=Decimal('15.00')
        )

        self.assertEqual(uso.voucher, voucher)
        self.assertEqual(uso.cliente, self.cliente)
        self.assertEqual(uso.valor_desconto, Decimal('15.00'))


from vouchers.services import (
    gerar_codigo_voucher,
    criar_voucher,
    editar_voucher,
    inativar_voucher,
    ativar_voucher,
    registrar_uso_voucher,
    validar_voucher,
)
from vouchers.services.comissoes_parceiro import gerar_comissao_parceiro_por_uso

from vouchers.selectors import (
    get_vouchers,
    get_vouchers_ativos,
)

class VoucherServiceSelectorTest(TestCase):

    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Services'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Services'
        )

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Services',
            cpf='98765432100'
        )

        self.User = get_user_model()

        self.usuario = self.User.objects.create_user(
            username='usuario_services',
            password='123456',
            matriz=self.matriz
        )

        self.usuario.lojas.add(self.loja)

    def test_gerar_codigo_voucher(self):
        codigo = gerar_codigo_voucher()

        self.assertTrue(codigo.startswith('VCH-'))
        self.assertEqual(len(codigo), 13)

    def test_criar_voucher(self):
        hoje = timezone.localdate()

        voucher = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Service',
                'descricao': 'Teste service',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('20.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        self.assertIsNotNone(voucher.codigo)
        self.assertEqual(voucher.matriz, self.matriz)
        self.assertEqual(voucher.valor, Decimal('20.00'))

    def test_editar_voucher(self):
        hoje = timezone.localdate()

        voucher = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Original',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        editar_voucher(
            voucher=voucher,
            dados={
                'cliente': None,
                'nome': 'Voucher Editado',
                'descricao': 'Alterado',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('15.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=20),
                'uso_unico_por_cliente': False,
                'limite_utilizacao': 10,
            },
            usuario_executor=self.usuario
        )

        voucher.refresh_from_db()

        self.assertEqual(voucher.nome, 'Voucher Editado')
        self.assertEqual(voucher.valor, Decimal('15.00'))
        self.assertEqual(voucher.limite_utilizacao, 10)

    def test_ativar_inativar_voucher(self):
        hoje = timezone.localdate()

        voucher = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Status',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        inativar_voucher(
            voucher=voucher,
            usuario_executor=self.usuario
        )

        voucher.refresh_from_db()
        self.assertEqual(voucher.status, Voucher.Status.INATIVO)

        ativar_voucher(
            voucher=voucher,
            usuario_executor=self.usuario
        )

        voucher.refresh_from_db()
        self.assertEqual(voucher.status, Voucher.Status.ATIVO)

    def test_validar_voucher(self):
        hoje = timezone.localdate()

        voucher = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Validação',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        valido, mensagem = validar_voucher(
            voucher=voucher
        )

        self.assertTrue(valido)
        self.assertEqual(mensagem, '')

    def test_get_vouchers_por_matriz(self):
        hoje = timezone.localdate()

        criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Selector',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        vouchers = get_vouchers(
            matriz=self.matriz
        )

        self.assertEqual(vouchers.count(), 1)

    def test_get_vouchers_ativos(self):
        hoje = timezone.localdate()

        ativo = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Ativo',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        inativo = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None,
                'nome': 'Voucher Inativo',
                'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO,
                'valor': Decimal('10.00'),
                'percentual': None,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True,
                'limite_utilizacao': 5,
            },
            usuario_executor=self.usuario
        )

        inativar_voucher(
            voucher=inativo,
            usuario_executor=self.usuario
        )

        vouchers = get_vouchers_ativos(
            matriz=self.matriz
        )

        self.assertIn(ativo, vouchers)
        self.assertNotIn(inativo, vouchers)


    def test_registrar_uso_voucher_atualiza_historico_e_contador(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-USO-01',
            nome='Voucher Uso Oficial',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('20.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=2,
            total_utilizado=0
        )

        compra = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal('100.00'),
            percentual_cashback=Decimal('5.00'),
            valor_cashback=Decimal('5.00'),
            valor_utilizado=Decimal('0.00'),
            data_liberacao=hoje,
            data_expiracao=hoje + timedelta(days=30),
        )

        uso = registrar_uso_voucher(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            voucher=voucher,
            usuario=self.usuario,
            compra=compra,
            valor_compra=Decimal('100.00'),
            valor_desconto=Decimal('20.00'),
            observacao='Teste de uso oficial.'
        )

        voucher.refresh_from_db()

        self.assertEqual(voucher.total_utilizado, 1)
        self.assertEqual(voucher.usos.count(), 1)
        self.assertEqual(uso.compra, compra)
        self.assertEqual(uso.valor_desconto, Decimal('20.00'))

class ParceiroComissaoServiceTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz Parceiro')
        self.loja = Loja.objects.create(matriz=self.matriz, nome='Loja Parceiro')
        self.cliente = Cliente.objects.create(matriz=self.matriz, loja_cadastro=self.loja, nome='Cliente Parceiro', cpf='11122233344')
        self.usuario = get_user_model().objects.create_user(username='usuario_parceiro', password='123456', matriz=self.matriz)
        self.usuario.lojas.add(self.loja)
        hoje = timezone.localdate()
        self.voucher = Voucher.objects.create(matriz=self.matriz, codigo='VCH-PARCEIRO', nome='Voucher Parceiro', tipo=Voucher.Tipo.VALOR_FIXO, valor=Decimal('20.00'), data_inicio=hoje, data_fim=hoje + timedelta(days=10), limite_utilizacao=20, total_utilizado=0)

    def criar_parceiro(self, **kwargs):
        dados = {'matriz': self.matriz, 'nome': 'Parceiro Teste', 'tipo_comissao': Parceiro.TipoComissao.PERCENTUAL, 'percentual_comissao': Decimal('10.00'), 'base_calculo': Parceiro.BaseCalculo.APOS_DESCONTO, 'ativo': True}
        dados.update(kwargs)
        parceiro = Parceiro(**dados)
        parceiro.full_clean()
        parceiro.save()
        return parceiro

    def criar_uso(self, parceiro=None):
        return UsoVoucher.objects.create(matriz=self.matriz, voucher=self.voucher, cliente=self.cliente, loja=self.loja, usuario=self.usuario, parceiro=parceiro, valor_compra=Decimal('100.00'), valor_desconto=Decimal('20.00'))

    def test_percentual_apos_desconto_e_idempotencia(self):
        parceiro = self.criar_parceiro()
        uso = self.criar_uso(parceiro)
        a = gerar_comissao_parceiro_por_uso(uso_voucher=uso)
        b = gerar_comissao_parceiro_por_uso(uso_voucher=uso)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(a.valor_base, Decimal('80.00'))
        self.assertEqual(a.valor_comissao, Decimal('8.00'))
        self.assertEqual(ComissaoParceiro.objects.filter(uso_voucher=uso).count(), 1)

    def test_percentual_base_bruto(self):
        parceiro = self.criar_parceiro(nome='Parceiro Bruto', base_calculo=Parceiro.BaseCalculo.BRUTO)
        c = gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso(parceiro))
        self.assertEqual(c.valor_base, Decimal('100.00'))
        self.assertEqual(c.valor_comissao, Decimal('10.00'))

    def test_valor_fixo(self):
        parceiro = self.criar_parceiro(nome='Parceiro Fixo', tipo_comissao=Parceiro.TipoComissao.VALOR_FIXO, percentual_comissao=None, valor_comissao=Decimal('7.50'))
        c = gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso(parceiro))
        self.assertEqual(c.valor_comissao, Decimal('7.50'))

    def test_sem_parceiro_nao_gera(self):
        self.assertIsNone(gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso()))

    def test_inativo_e_expirado_nao_geram(self):
        hoje = timezone.localdate()
        inativo = self.criar_parceiro(nome='Parceiro Inativo', ativo=False)
        expirado = self.criar_parceiro(nome='Parceiro Expirado', vigencia_inicio=hoje-timedelta(days=10), vigencia_fim=hoje-timedelta(days=1))
        self.assertIsNone(gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso(inativo)))
        self.assertIsNone(gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso(expirado)))

    def test_matriz_divergente_nao_gera(self):
        outra = Matriz.objects.create(nome='Outra Matriz Parceiro')
        parceiro = self.criar_parceiro(nome='Parceiro Divergente')
        parceiro.matriz = outra
        parceiro.save(update_fields=['matriz'])
        self.assertIsNone(gerar_comissao_parceiro_por_uso(uso_voucher=self.criar_uso(parceiro)))

    def test_snapshot_permanece(self):
        parceiro = self.criar_parceiro(nome='Parceiro Snapshot', base_calculo=Parceiro.BaseCalculo.BRUTO)
        uso = self.criar_uso(parceiro)
        c = gerar_comissao_parceiro_por_uso(uso_voucher=uso)
        parceiro.percentual_comissao = Decimal('25.00')
        parceiro.base_calculo = Parceiro.BaseCalculo.APOS_DESCONTO
        parceiro.save()
        mesma = gerar_comissao_parceiro_por_uso(uso_voucher=uso)
        mesma.refresh_from_db()
        self.assertEqual(mesma.pk, c.pk)
        self.assertEqual(mesma.percentual_aplicado, Decimal('10.0000'))
        self.assertEqual(mesma.valor_base, Decimal('100.00'))
        self.assertEqual(mesma.valor_comissao, Decimal('10.00'))

    def test_registrar_uso_gera_comissao_automaticamente(self):
        parceiro = self.criar_parceiro(nome='Parceiro Integrado')
        self.voucher.parceiro = parceiro
        self.voucher.save(update_fields=['parceiro'])
        uso = registrar_uso_voucher(matriz=self.matriz, loja=self.loja, cliente=self.cliente, voucher=self.voucher, usuario=self.usuario, compra=None, valor_compra=Decimal('100.00'), valor_desconto=Decimal('20.00'), observacao='Teste integrado parceiro.')
        c = ComissaoParceiro.objects.get(uso_voucher=uso)
        self.assertEqual(uso.parceiro, parceiro)
        self.assertEqual(c.valor_base, Decimal('80.00'))
        self.assertEqual(c.valor_comissao, Decimal('8.00'))

class ParceiroVoucherAdminTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz Admin Parceiro')
        self.outra_matriz = Matriz.objects.create(nome='Outra Matriz Admin Parceiro')
        self.parceiro = Parceiro.objects.create(
            matriz=self.matriz, nome='Parceiro Matriz',
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            percentual_comissao=Decimal('10.00'),
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
        )
        self.parceiro_outra = Parceiro.objects.create(
            matriz=self.outra_matriz, nome='Parceiro Outra Matriz',
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            percentual_comissao=Decimal('5.00'),
            base_calculo=Parceiro.BaseCalculo.BRUTO,
        )

    def test_voucher_form_lista_apenas_parceiros_ativos_da_matriz(self):
        Parceiro.objects.create(
            matriz=self.matriz, nome='Parceiro Inativo',
            tipo_comissao=Parceiro.TipoComissao.VALOR_FIXO,
            valor_comissao=Decimal('3.00'),
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            ativo=False,
        )
        form = VoucherForm(matriz=self.matriz)
        ids = set(form.fields['parceiro'].queryset.values_list('id', flat=True))
        self.assertIn(self.parceiro.id, ids)
        self.assertNotIn(self.parceiro_outra.id, ids)
        self.assertEqual(len(ids), 1)

    def test_criar_voucher_persiste_parceiro(self):
        hoje = timezone.localdate()
        voucher = criar_voucher(
            matriz=self.matriz,
            dados={
                'cliente': None, 'parceiro': self.parceiro,
                'nome': 'Voucher com Parceiro', 'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO, 'valor': Decimal('10.00'),
                'percentual': None, 'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True, 'limite_utilizacao': 5,
                'lojas': [],
            },
            usuario_executor=None,
        )
        self.assertEqual(voucher.parceiro, self.parceiro)

    def test_editar_voucher_persiste_parceiro(self):
        hoje = timezone.localdate()
        voucher = Voucher.objects.create(
            matriz=self.matriz, codigo='VCH-EDIT-PARC', nome='Voucher Edit',
            tipo=Voucher.Tipo.VALOR_FIXO, valor=Decimal('10.00'),
            data_inicio=hoje, data_fim=hoje + timedelta(days=10),
            limite_utilizacao=5,
        )
        editar_voucher(
            voucher=voucher,
            dados={
                'cliente': None, 'parceiro': self.parceiro,
                'nome': voucher.nome, 'descricao': '',
                'tipo': Voucher.Tipo.VALOR_FIXO, 'valor': Decimal('10.00'),
                'percentual': None, 'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=10),
                'uso_unico_por_cliente': True, 'limite_utilizacao': 5,
                'lojas': [],
            },
            usuario_executor=None,
        )
        voucher.refresh_from_db()
        self.assertEqual(voucher.parceiro, self.parceiro)
