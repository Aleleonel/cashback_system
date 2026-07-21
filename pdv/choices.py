from django.db import models


class TipoOperacaoVenda(models.TextChoices):
    VENDA = "venda", "Venda"
    ORCAMENTO = "orcamento", "Orcamento"
    ESPERA = "espera", "Venda em espera"


class StatusOperacaoVenda(models.TextChoices):
    RASCUNHO = "rascunho", "Rascunho"
    ORCAMENTO = "orcamento", "Orcamento"
    ESPERA = "espera", "Em espera"
    ABERTA = "aberta", "Aberta"
    PAGAMENTO = "pagamento", "Em pagamento"
    FINALIZADA = "finalizada", "Finalizada"
    CANCELADA = "cancelada", "Cancelada"
    EXPIRADA = "expirada", "Expirada"


class ModalidadeComercial(models.TextChoices):
    VAREJO = "varejo", "Varejo"
    ATACADO = "atacado", "Atacado"


class TipoEmissaoVenda(models.TextChoices):
    NAO_FISCAL = "nao_fiscal", "Nao fiscal"
    FISCAL = "fiscal", "Fiscal"


class StatusCaixa(models.TextChoices):
    ATIVO = "ativo", "Ativo"
    INATIVO = "inativo", "Inativo"


class StatusSessaoCaixa(models.TextChoices):
    ABERTA = "aberta", "Aberta"
    FECHADA = "fechada", "Fechada"
    CANCELADA = "cancelada", "Cancelada"


class TipoMovimentacaoCaixa(models.TextChoices):
    ABERTURA = "abertura", "Abertura"
    VENDA = "venda", "Venda"
    SUPRIMENTO = "suprimento", "Suprimento"
    SANGRIA = "sangria", "Sangria"
    ESTORNO = "estorno", "Estorno"
    FECHAMENTO = "fechamento", "Fechamento"


class TipoFormaPagamento(models.TextChoices):
    DINHEIRO = "dinheiro", "Dinheiro"
    PIX = "pix", "PIX"
    CARTAO_CREDITO = "cartao_credito", "Cartao de credito"
    CARTAO_DEBITO = "cartao_debito", "Cartao de debito"
    CREDIARIO = "crediario", "Crediario"
    VALE = "vale", "Vale"
    CORTESIA = "cortesia", "Cortesia"
    OUTRO = "outro", "Outro"
