from abc import ABC, abstractmethod

import pandas as pd

from .exceptions import ErroLeituraPlanilha
from .resultado import ResultadoImportacao
from .validacoes import normalizar_coluna


class ImportadorBase(ABC):
    """
    Fluxo compartilhado para validação de planilhas.

    Cada domínio deve definir:
    - colunas_esperadas;
    - validar_linha().
    """

    colunas_esperadas = {}

    def __init__(
        self,
        *,
        arquivo,
    ):
        self.arquivo = arquivo

    def ler_dataframe(self):
        try:
            return pd.read_excel(
                self.arquivo,
                dtype=object,
            )
        except Exception as erro:
            raise ErroLeituraPlanilha(
                'Não foi possível ler a planilha enviada.'
            ) from erro

    def construir_mapa_colunas(
        self,
        dataframe,
    ):
        return {
            normalizar_coluna(coluna): coluna
            for coluna in dataframe.columns
        }

    def validar_estrutura(
        self,
        mapa_colunas,
    ):
        return [
            nome_exibicao
            for chave, nome_exibicao
            in self.colunas_esperadas.items()
            if normalizar_coluna(chave)
            not in mapa_colunas
        ]

    def processar(self):
        try:
            dataframe = self.ler_dataframe()
        except ErroLeituraPlanilha as erro:
            return ResultadoImportacao.falha_estrutura(
                str(erro)
            )

        mapa_colunas = self.construir_mapa_colunas(
            dataframe
        )

        colunas_ausentes = self.validar_estrutura(
            mapa_colunas
        )

        if colunas_ausentes:
            return ResultadoImportacao.falha_estrutura(
                (
                    'Colunas obrigatórias ausentes: '
                    + ', '.join(colunas_ausentes)
                    + '.'
                )
            )

        resultado = ResultadoImportacao()

        contadores_status = {}

        for indice, linha_planilha in dataframe.iterrows():
            numero_linha = indice + 2

            linha = self.validar_linha(
                numero_linha=numero_linha,
                linha_planilha=linha_planilha,
                mapa_colunas=mapa_colunas,
            )

            linha.setdefault(
                'linha',
                numero_linha,
            )
            linha.setdefault(
                'erros',
                [],
            )
            linha.setdefault(
                'valido',
                not linha['erros'],
            )

            status = linha.get(
                'status',
                'sem_status',
            )

            contadores_status[status] = (
                contadores_status.get(status, 0)
                + 1
            )

            resultado.adicionar_linha(
                linha
            )

        validos = sum(
            1
            for linha in resultado.linhas
            if linha.get('valido')
        )

        invalidos = (
            len(resultado.linhas)
            - validos
        )

        resumo = {
            'total': len(resultado.linhas),
            'validos': validos,
            'invalidos': invalidos,
        }

        resumo.update(
            contadores_status
        )

        resultado.atualizar_resumo(
            **resumo
        )

        return resultado

    @abstractmethod
    def validar_linha(
        self,
        *,
        numero_linha,
        linha_planilha,
        mapa_colunas,
    ):
        """
        Retorna um dicionário serializável contendo,
        no mínimo, erros, válido e status.
        """
        raise NotImplementedError
