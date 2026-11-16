"""F32P4H88D: contratos iniciais da conciliacao manual de cartoes.
Testes de caracterizacao RED: nao modificam dados operacionais.
"""
from pathlib import Path
from django.test import SimpleTestCase
from pdv.choices import TipoFormaPagamento


class ContratoConciliacaoManualCartoes(SimpleTestCase):
    def test_formas_basicas_cartao_devem_gerar_recebiveis(self):
        from pdv.services.vendas import fechamento
        from unittest.mock import patch
        from types import SimpleNamespace

        capturados = []
        class Manager:
            def get_or_create(self, **kwargs):
                capturados.append(kwargs)
                return (SimpleNamespace(), True)
            def filter(self, **kwargs):
                return self
            def order_by(self, *args):
                return []
        with patch.object(fechamento.FormaPagamento, 'objects', Manager()):
            fechamento.garantir_formas_pagamento_basicas(matriz=object())
        por_tipo = {c['defaults']['tipo']: c['defaults'] for c in capturados}
        for tipo in (TipoFormaPagamento.CARTAO_CREDITO, TipoFormaPagamento.CARTAO_DEBITO):
            with self.subTest(tipo=tipo):
                self.assertTrue(por_tipo[tipo].get('gera_contas_receber', False),
                                'Cartoes precisam originar recebiveis pendentes de conciliacao')
                self.assertFalse(por_tipo[tipo]['movimenta_caixa'])

    def test_pix_nao_gera_recebivel_de_cartao(self):
        from pdv.services.vendas import fechamento
        from unittest.mock import patch
        from types import SimpleNamespace
        capturados = []
        class Manager:
            def get_or_create(self, **kwargs):
                capturados.append(kwargs)
                return (SimpleNamespace(), True)
            def filter(self, **kwargs): return self
            def order_by(self, *args): return []
        with patch.object(fechamento.FormaPagamento, 'objects', Manager()):
            fechamento.garantir_formas_pagamento_basicas(matriz=object())
        pix = next(c['defaults'] for c in capturados if c['defaults']['tipo'] == TipoFormaPagamento.PIX)
        self.assertFalse(pix['movimenta_caixa'])
        self.assertFalse(pix.get('gera_contas_receber', False))

    def test_recebivel_usa_chave_idempotente_por_pagamento(self):
        raiz = Path(__file__).resolve().parents[2]
        codigo = (raiz / 'pdv/services/vendas/finalizacao.py').read_text(encoding='utf-8')
        self.assertIn('venda-pagamento:{pagamento.uuid}', codigo)
        self.assertIn('forma_pagamento__gera_contas_receber=True', codigo)
