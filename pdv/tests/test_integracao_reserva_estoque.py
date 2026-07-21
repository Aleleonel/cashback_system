from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.test import SimpleTestCase

from pdv.services.vendas.estoque import (
    _gerar_chave_reserva,
    _origem_id_item,
)


class IntegracaoReservaEstoqueHelpersTests(SimpleTestCase):
    def test_origem_id_usa_uuid_do_item(self):
        item = SimpleNamespace(uuid=uuid4())

        self.assertEqual(_origem_id_item(item), str(item.uuid))

    @patch("pdv.services.vendas.estoque.uuid.uuid4")
    def test_chave_sem_data_tem_prefixo_estavel(self, uuid_mock):
        uuid_mock.return_value.hex = "abc123"
        item = SimpleNamespace(
            uuid=uuid4(),
            atualizado_em=None,
        )

        chave = _gerar_chave_reserva(item)

        self.assertEqual(
            chave,
            f"pdv:item:{item.uuid}:reserva:abc123",
        )
