from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from vouchers.models import ComissaoParceiro, Parceiro, UsoVoucher, Voucher


class F31ConsolidacaoComissoesParceirosContractTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F31")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F31")
        User = get_user_model()
        self.usuario = User.objects.create_user(username="f31user", password="teste-f31")
        self.cliente = Cliente.objects.create(
            matriz=self.matriz, loja_cadastro=self.loja, nome="Cliente F31"
        )
        self.parceiro = Parceiro.objects.create(
            matriz=self.matriz,
            nome="Parceiro F31",
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            percentual_comissao=Decimal("5.0000"),
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            ativo=True,
        )
        hoje = timezone.localdate()
        self.voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo="F31PARC",
            nome="Voucher F31 Parceiro",
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal("10.00"),
            percentual=None,
            data_inicio=hoje - timedelta(days=60),
            data_fim=hoje + timedelta(days=60),
            limite_utilizacao=100,
            total_utilizado=0,
            parceiro=self.parceiro,
        )

    def _comissao(self, compra, desconto, base, valor):
        uso = UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=self.voucher,
            cliente=self.cliente,
            loja=self.loja,
            usuario=self.usuario,
            parceiro=self.parceiro,
            valor_compra=Decimal(compra),
            valor_desconto=Decimal(desconto),
        )
        return ComissaoParceiro.objects.create(
            uso_voucher=uso,
            matriz=self.matriz,
            parceiro=self.parceiro,
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            valor_base=Decimal(base),
            percentual_aplicado=Decimal("5.0000"),
            valor_comissao=Decimal(valor),
        )

    def test_consolida_multiplas_vendas_do_mes_em_uma_linha_por_parceiro(self):
        self._comissao("299.00", "10.00", "289.00", "14.45")
        self._comissao("500.00", "10.00", "490.00", "24.50")

        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros

        hoje = timezone.localdate()
        grupos = consolidar_comissoes_parceiros(
            matriz=self.matriz, ano=hoje.year, mes=hoje.month
        )

        self.assertEqual(len(grupos), 1)
        grupo = grupos[0]
        self.assertEqual(grupo["parceiro_id"], self.parceiro.pk)
        self.assertEqual(grupo["quantidade_vendas"], 2)
        self.assertEqual(grupo["total_vendas"], Decimal("799.00"))
        self.assertEqual(grupo["total_descontos"], Decimal("20.00"))
        self.assertEqual(grupo["total_base"], Decimal("779.00"))
        self.assertEqual(grupo["total_comissao"], Decimal("38.95"))
        self.assertNotIn("comissoes_ids", grupo)

    def test_consolidacao_soma_snapshots_e_nao_recalcula_por_percentual_atual(self):
        primeira = self._comissao("100.00", "10.00", "90.00", "4.50")
        primeira.percentual_aplicado = Decimal("5.0000")
        primeira.save(update_fields=["percentual_aplicado"])

        segunda = self._comissao("200.00", "20.00", "180.00", "18.00")
        segunda.percentual_aplicado = Decimal("10.0000")
        segunda.save(update_fields=["percentual_aplicado"])

        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros

        hoje = timezone.localdate()
        grupo = consolidar_comissoes_parceiros(
            matriz=self.matriz, ano=hoje.year, mes=hoje.month
        )[0]

        self.assertEqual(grupo["total_base"], Decimal("270.00"))
        self.assertEqual(grupo["total_comissao"], Decimal("22.50"))
    def test_isola_parceiros_na_mesma_competencia(self):
        self._comissao("100.00", "10.00", "90.00", "4.50")
        parceiro2 = Parceiro.objects.create(
            matriz=self.matriz,
            nome="Parceiro F31 B",
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            percentual_comissao=Decimal("10.0000"),
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            ativo=True,
        )
        uso = UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=self.voucher,
            cliente=self.cliente,
            loja=self.loja,
            usuario=self.usuario,
            parceiro=parceiro2,
            valor_compra=Decimal("200.00"),
            valor_desconto=Decimal("20.00"),
        )
        ComissaoParceiro.objects.create(
            uso_voucher=uso,
            matriz=self.matriz,
            parceiro=parceiro2,
            tipo_comissao=Parceiro.TipoComissao.PERCENTUAL,
            base_calculo=Parceiro.BaseCalculo.APOS_DESCONTO,
            valor_base=Decimal("180.00"),
            percentual_aplicado=Decimal("10.0000"),
            valor_comissao=Decimal("18.00"),
        )
        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros
        hoje = timezone.localdate()
        grupos = consolidar_comissoes_parceiros(matriz=self.matriz, ano=hoje.year, mes=hoje.month)
        self.assertEqual(len(grupos), 2)
        self.assertEqual({g["parceiro_id"] for g in grupos}, {self.parceiro.pk, parceiro2.pk})

    def test_isola_matrizes(self):
        self._comissao("100.00", "10.00", "90.00", "4.50")
        outra = Matriz.objects.create(nome="Outra Matriz F31")
        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros
        hoje = timezone.localdate()
        grupos = consolidar_comissoes_parceiros(matriz=outra, ano=hoje.year, mes=hoje.month)
        self.assertEqual(grupos, [])

    def test_isola_competencia_mensal(self):
        comissao = self._comissao("100.00", "10.00", "90.00", "4.50")
        hoje = timezone.localdate()
        if hoje.month == 1:
            ano_anterior, mes_anterior = hoje.year - 1, 12
        else:
            ano_anterior, mes_anterior = hoje.year, hoje.month - 1
        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros
        atual = consolidar_comissoes_parceiros(matriz=self.matriz, ano=hoje.year, mes=hoje.month)
        anterior = consolidar_comissoes_parceiros(matriz=self.matriz, ano=ano_anterior, mes=mes_anterior)
        self.assertEqual(len(atual), 1)
        self.assertNotIn("comissoes_ids", atual[0])
        self.assertEqual(anterior, [])


    def test_resumo_usa_competencia_do_uso_e_nao_materializa_ids(self):
        from datetime import timedelta
        from django.utils import timezone
        from vouchers.models import ComissaoParceiro, UsoVoucher
        from configuracoes.services_comissoes_parceiros import consolidar_comissoes_parceiros

        comissao = self._comissao("100.00", "10.00", "90.00", "4.50")
        self.assertIsNotNone(comissao)
        uso = comissao.uso_voucher
        agora = timezone.now()
        mes_anterior = (agora.replace(day=1) - timedelta(days=1)).replace(day=15)
        UsoVoucher.objects.filter(pk=uso.pk).update(criado_em=mes_anterior)
        ComissaoParceiro.objects.filter(pk=comissao.pk).update(criado_em=agora)

        grupos = consolidar_comissoes_parceiros(
            matriz=self.matriz, ano=mes_anterior.year, mes=mes_anterior.month
        )
        self.assertTrue(any(g["parceiro_id"] == comissao.parceiro_id for g in grupos))
        for grupo in grupos:
            self.assertNotIn("comissoes_ids", grupo)


    def test_detalhes_parceiro_competencia_sao_paginados(self):
        from configuracoes.services_comissoes_parceiros import listar_detalhes_comissoes_parceiro

        for i in range(25):
            self._comissao("100.00", "10.00", "90.00", "4.50")

        hoje = timezone.localdate()
        pagina = listar_detalhes_comissoes_parceiro(
            matriz=self.matriz,
            parceiro_id=self.parceiro.pk,
            ano=hoje.year,
            mes=hoje.month,
            pagina=2,
            por_pagina=10,
        )

        self.assertEqual(pagina.paginator.count, 25)
        self.assertEqual(pagina.number, 2)
        self.assertEqual(len(pagina.object_list), 10)
        detalhe = pagina.object_list[0]
        self.assertEqual(detalhe.parceiro_id, self.parceiro.pk)
        self.assertEqual(detalhe.uso_voucher.voucher_id, self.voucher.pk)
        self.assertEqual(detalhe.uso_voucher.loja_id, self.loja.pk)

    def test_detalhes_respeitam_matriz_parceiro_e_competencia(self):
        from configuracoes.services_comissoes_parceiros import listar_detalhes_comissoes_parceiro

        self._comissao("100.00", "10.00", "90.00", "4.50")
        hoje = timezone.localdate()
        outra = Matriz.objects.create(nome="Outra Matriz Detalhes F31")

        pagina = listar_detalhes_comissoes_parceiro(
            matriz=outra,
            parceiro_id=self.parceiro.pk,
            ano=hoje.year,
            mes=hoje.month,
            pagina=1,
            por_pagina=10,
        )
        self.assertEqual(pagina.paginator.count, 0)

class F31UiConsolidadaSourceContractTests(TestCase):
    def test_view_integra_servico_consolidado_e_competencia(self):
        from pathlib import Path
        from configuracoes import views

        fonte = Path(views.__file__).read_text(encoding="utf-8")
        self.assertIn("consolidar_comissoes_parceiros", fonte)
        self.assertIn("comissoes_parceiros_consolidadas", fonte)
        self.assertIn("competencia_parceiros", fonte)

    def test_template_renderiza_resumo_e_nao_itera_lista_individual(self):
        from pathlib import Path
        from django.conf import settings

        template = (
            Path(settings.BASE_DIR)
            / "configuracoes"
            / "templates"
            / "configuracoes"
            / "comissoes.html"
        ).read_text(encoding="utf-8")

        self.assertIn("comissoes_parceiros_consolidadas", template)
        self.assertIn("quantidade_vendas", template)
        self.assertIn("total_vendas", template)
        self.assertIn("total_descontos", template)
        self.assertIn("total_base", template)
        self.assertIn("total_comissao", template)
        self.assertNotIn("{% for comissao_parceiro in comissoes_parceiros %}", template)
    def test_ui_oferece_ver_detalhes_sem_materializar_lista_principal(self):
        from pathlib import Path
        from configuracoes import views

        template = (
            Path(views.__file__).resolve().parent
            / "templates"
            / "configuracoes"
            / "comissoes.html"
        ).read_text(encoding="utf-8")
        view_source = Path(views.__file__).read_text(encoding="utf-8")

        self.assertIn("Ver detalhes", template)
        self.assertIn("parceiro_detalhes", template)
        self.assertIn("listar_detalhes_comissoes_parceiro", view_source)
        self.assertIn("parceiro_detalhes", view_source)
        self.assertNotIn("comissoes_ids", template)
