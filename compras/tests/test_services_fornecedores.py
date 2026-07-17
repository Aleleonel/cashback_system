from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.models import RegistroAuditoria
from empresas.models import Matriz

from compras.choices import StatusFornecedor
from compras.models import Fornecedor
from compras.services import (
    alterar_status_fornecedor,
    criar_fornecedor,
    editar_fornecedor,
)


Usuario = get_user_model()


class FornecedorServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Services'
        )

        self.usuario = Usuario.objects.create_user(
            username='admin_compras',
            password='senha-segura',
            matriz=self.matriz,
        )

    def dados_validos(self, **alteracoes):
        dados = {
            'razao_social': ' Fornecedor Teste LTDA ',
            'nome_fantasia': ' Fornecedor Teste ',
            'cnpj': '11.222.333/0001-81',
            'inscricao_estadual': ' 123456 ',
            'telefone': ' (11) 3333-4444 ',
            'whatsapp': ' (11) 99999-8888 ',
            'email': ' COMPRAS@EXEMPLO.COM ',
            'contato_principal': ' Maria ',
            'status': StatusFornecedor.ATIVO,
            'observacoes': ' Fornecedor homologado ',
        }

        dados.update(alteracoes)
        return dados

    def test_cria_fornecedor_normalizado(self):
        fornecedor = criar_fornecedor(
            matriz=self.matriz,
            dados=self.dados_validos(),
            usuario=self.usuario,
        )

        self.assertEqual(
            fornecedor.razao_social,
            'Fornecedor Teste LTDA',
        )
        self.assertEqual(
            fornecedor.cnpj,
            '11222333000181',
        )
        self.assertEqual(
            fornecedor.email,
            'compras@exemplo.com',
        )

    def test_criacao_registra_auditoria(self):
        fornecedor = criar_fornecedor(
            matriz=self.matriz,
            dados=self.dados_validos(),
            usuario=self.usuario,
        )

        auditoria = RegistroAuditoria.objects.get(
            recurso='compras.fornecedor',
            recurso_id=str(fornecedor.uuid),
            acao=RegistroAuditoria.ACAO_CRIAR,
        )

        self.assertEqual(
            auditoria.matriz,
            self.matriz,
        )

    def test_rejeita_cnpj_invalido(self):
        with self.assertRaises(ValidationError):
            criar_fornecedor(
                matriz=self.matriz,
                dados=self.dados_validos(
                    cnpj='11.111.111/1111-11'
                ),
                usuario=self.usuario,
            )

    def test_edita_fornecedor(self):
        fornecedor = criar_fornecedor(
            matriz=self.matriz,
            dados=self.dados_validos(),
            usuario=self.usuario,
        )

        fornecedor = editar_fornecedor(
            fornecedor=fornecedor,
            dados=self.dados_validos(
                razao_social='Fornecedor Atualizado LTDA',
            ),
            usuario=self.usuario,
        )

        self.assertEqual(
            fornecedor.razao_social,
            'Fornecedor Atualizado LTDA',
        )

    def test_altera_status(self):
        fornecedor = criar_fornecedor(
            matriz=self.matriz,
            dados=self.dados_validos(),
            usuario=self.usuario,
        )

        fornecedor = alterar_status_fornecedor(
            fornecedor=fornecedor,
            status=StatusFornecedor.BLOQUEADO,
            usuario=self.usuario,
        )

        self.assertEqual(
            fornecedor.status,
            StatusFornecedor.BLOQUEADO,
        )

    def test_falha_na_auditoria_desfaz_criacao(self):
        with patch(
            (
                'compras.services.fornecedores.'
                'registrar_auditoria'
            ),
            side_effect=RuntimeError(
                'Falha simulada de auditoria'
            ),
        ):
            with self.assertRaises(RuntimeError):
                criar_fornecedor(
                    matriz=self.matriz,
                    dados=self.dados_validos(),
                    usuario=self.usuario,
                )

        self.assertFalse(
            Fornecedor.objects.exists()
        )