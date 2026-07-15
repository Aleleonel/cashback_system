class ErroImportacao(Exception):
    """Erro base da infraestrutura de importação."""


class ErroEstruturaPlanilha(ErroImportacao):
    """A planilha não possui a estrutura mínima esperada."""


class ErroLeituraPlanilha(ErroImportacao):
    """Não foi possível abrir ou interpretar a planilha."""


class ErroConfirmacaoImportacao(ErroImportacao):
    """A importação não pode ser confirmada no estado atual."""
