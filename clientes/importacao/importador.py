from core.importacao import (
    ImportadorBase,
    limpar_numero,
    limpar_texto,
    serializar_data_sessao,
    converter_data,
)
from clientes.models import Cliente


class ImportadorClientes(ImportadorBase):
    colunas_esperadas = {
        'nome': 'Nome',
        'cpf': 'CPF',
        'nascimento': 'Nascimento',
        'celular': 'Celular',
        'email': 'E-mail',
    }

    def __init__(
        self,
        *,
        arquivo,
        matriz,
    ):
        super().__init__(
            arquivo=arquivo
        )

        self.matriz = matriz

        self.cpfs_existentes = set(
            Cliente.objects.filter(
                matriz=matriz
            ).values_list(
                'cpf_normalizado',
                flat=True
            )
        )

    def _obter_valor(
        self,
        *,
        linha_planilha,
        mapa_colunas,
        chave,
    ):
        coluna_original = mapa_colunas[
            chave
        ]

        return linha_planilha.get(
            coluna_original
        )

    def validar_linha(
        self,
        *,
        numero_linha,
        linha_planilha,
        mapa_colunas,
    ):
        nome = limpar_texto(
            self._obter_valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='nome',
            )
        )

        cpf = limpar_numero(
            self._obter_valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='cpf',
            )
        )

        nascimento_original = self._obter_valor(
            linha_planilha=linha_planilha,
            mapa_colunas=mapa_colunas,
            chave='nascimento',
        )

        nascimento = converter_data(
            nascimento_original
        )

        celular = limpar_numero(
            self._obter_valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='celular',
            )
        )

        email = limpar_texto(
            self._obter_valor(
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
                chave='email',
            )
        )

        erros = []

        if not nome:
            erros.append(
                'Nome obrigatório.'
            )

        if nome and len(nome.split()) < 2:
            erros.append(
                'Informe nome completo.'
            )

        if not cpf:
            erros.append(
                'CPF obrigatório.'
            )

        if cpf and len(cpf) != 11:
            erros.append(
                'CPF deve conter 11 números.'
            )

        nascimento_informado = limpar_texto(
            nascimento_original
        )

        if (
            nascimento_informado
            and nascimento is None
        ):
            erros.append(
                'Nascimento inválido.'
            )

        if email and '@' not in email:
            erros.append(
                'E-mail inválido.'
            )

        status = (
            'atualizar'
            if cpf in self.cpfs_existentes
            else 'novo'
        )

        return {
            'linha': numero_linha,
            'nome': nome,
            'cpf': cpf,
            'nascimento': serializar_data_sessao(
                nascimento
            ),
            'celular': celular,
            'email': email,
            'status': status,
            'valido': not erros,
            'erros': erros,
        }


def validar_planilha_clientes_compartilhada(
    *,
    arquivo,
    matriz,
):
    resultado = ImportadorClientes(
        arquivo=arquivo,
        matriz=matriz,
    ).processar()

    return resultado.como_dict()
