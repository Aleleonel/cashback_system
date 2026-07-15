from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResultadoImportacao:
    estrutura_ok: bool = True
    linhas: list[dict[str, Any]] = field(
        default_factory=list
    )
    resumo: dict[str, int] = field(
        default_factory=dict
    )
    erros_estrutura: list[str] = field(
        default_factory=list
    )
    avisos: list[str] = field(
        default_factory=list
    )

    @property
    def possui_validos(self):
        return self.resumo.get(
            'validos',
            0
        ) > 0

    @property
    def total(self):
        return self.resumo.get(
            'total',
            len(self.linhas)
        )

    @property
    def validos(self):
        return self.resumo.get(
            'validos',
            0
        )

    @property
    def invalidos(self):
        return self.resumo.get(
            'invalidos',
            0
        )

    @property
    def erro_estrutura(self):
        if not self.erros_estrutura:
            return None

        return ' '.join(
            self.erros_estrutura
        )

    def adicionar_linha(self, linha):
        self.linhas.append(linha)

    def adicionar_erro_estrutura(self, mensagem):
        self.estrutura_ok = False
        self.erros_estrutura.append(
            str(mensagem)
        )

    def adicionar_aviso(self, mensagem):
        self.avisos.append(
            str(mensagem)
        )

    def atualizar_resumo(self, **valores):
        self.resumo.update(valores)

    def como_dict(self):
        """
        Mantém compatibilidade com o formato atualmente
        utilizado pela importação de Clientes.
        """
        return {
            'valido': self.estrutura_ok,
            'estrutura_ok': self.estrutura_ok,
            'erro_estrutura': self.erro_estrutura,
            'erros_estrutura': list(
                self.erros_estrutura
            ),
            'linhas': list(self.linhas),
            'resumo': dict(self.resumo),
            'avisos': list(self.avisos),
            'possui_validos': self.possui_validos,
        }

    @classmethod
    def falha_estrutura(cls, mensagens):
        if isinstance(mensagens, str):
            mensagens = [mensagens]

        return cls(
            estrutura_ok=False,
            erros_estrutura=list(mensagens),
            resumo={
                'total': 0,
                'validos': 0,
                'invalidos': 0,
            },
        )
