"""Testes focais de contrato para o nucleo de repasse (F32P4H88P)."""
from decimal import Decimal
from unittest.mock import Mock, patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from financeiro.conciliacao_adquirente import _dinheiro, registrar_repasse_adquirente
from financeiro._contexto_repasse import autorizar_estorno_repasse, estorno_repasse_autorizado


class ContratosRepasseAdquirente(TestCase):
    def test_dinheiro_duas_casas(self):
        self.assertEqual(_dinheiro('12.34', 'valor'), Decimal('12.34'))

    def test_dinheiro_rejeita_mais_de_duas_casas(self):
        with self.assertRaises(ValidationError):
            _dinheiro('12.345', 'valor')

    def test_dinheiro_rejeita_valor_negativo(self):
        with self.assertRaises(ValidationError):
            _dinheiro('-0.01', 'valor')

    def test_dinheiro_rejeita_nan(self):
        with self.assertRaises(ValidationError):
            _dinheiro('NaN', 'valor')

    def test_dinheiro_rejeita_infinito(self):
        with self.assertRaises(ValidationError):
            _dinheiro('Infinity', 'valor')

    def test_dinheiro_zero_apenas_quando_permitido(self):
        with self.assertRaises(ValidationError):
            _dinheiro('0', 'valor')
        self.assertEqual(_dinheiro('0', 'valor', permitir_zero=True), Decimal('0.00'))

    def test_contexto_estorno_fechado_por_padrao(self):
        self.assertFalse(estorno_repasse_autorizado())
        with autorizar_estorno_repasse():
            self.assertTrue(estorno_repasse_autorizado())
        self.assertFalse(estorno_repasse_autorizado())

    def test_contexto_estorno_restaura_apos_excecao(self):
        with self.assertRaises(RuntimeError):
            with autorizar_estorno_repasse():
                raise RuntimeError('teste')
        self.assertFalse(estorno_repasse_autorizado())

    def _registrar(self, **kwargs):
        params = dict(parcela=Mock(), bruto='100.00', taxa='2.00', data='2026-11-09',
                      chave_idempotencia='teste-f32p4h88p', forma_pagamento=Mock(),
                      conta_financeira=Mock())
        params.update(kwargs)
        return registrar_repasse_adquirente(**params)

    def test_rejeita_chave_vazia_antes_de_gravar(self):
        with self.assertRaises(ValidationError):
            self._registrar(chave_idempotencia='')

    def test_rejeita_conta_financeira_ausente(self):
        with self.assertRaises(ValidationError):
            self._registrar(conta_financeira=None)

    def test_rejeita_taxa_igual_ao_bruto(self):
        with self.assertRaises(ValidationError):
            self._registrar(taxa='100.00')

    def test_rejeita_taxa_superior_ao_bruto(self):
        with self.assertRaises(ValidationError):
            self._registrar(taxa='100.01')
