from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import OrcamentoAtacado, StatusOrcamentoAtacado, TransicaoOrcamentoAtacado


TRANSICOES_PERMITIDAS = {
    StatusOrcamentoAtacado.RASCUNHO: {
        StatusOrcamentoAtacado.ENVIADO,
        StatusOrcamentoAtacado.CANCELADO,
    },
    StatusOrcamentoAtacado.ENVIADO: {
        StatusOrcamentoAtacado.APROVADO,
        StatusOrcamentoAtacado.RECUSADO,
        StatusOrcamentoAtacado.CANCELADO,
        StatusOrcamentoAtacado.EXPIRADO,
    },
    StatusOrcamentoAtacado.APROVADO: {
        StatusOrcamentoAtacado.PEDIDO_GERADO,
        StatusOrcamentoAtacado.CANCELADO,
    },
    StatusOrcamentoAtacado.PEDIDO_GERADO: set(),
    StatusOrcamentoAtacado.RECUSADO: set(),
    StatusOrcamentoAtacado.CANCELADO: set(),
    StatusOrcamentoAtacado.EXPIRADO: set(),
}


@transaction.atomic
def transicionar_orcamento(orcamento, destino, *, usuario=None, observacao=""):
    origem = orcamento.status
    permitidas = TRANSICOES_PERMITIDAS.get(origem, set())
    if destino not in permitidas:
        raise ValidationError(
            f"Transição de {origem} para {destino} não permitida."
        )

    agora = timezone.now()
    if destino == StatusOrcamentoAtacado.APROVADO and orcamento.esta_expirado:
        raise ValidationError("Orçamento expirado não pode ser aprovado.")

    campos_data = {
        StatusOrcamentoAtacado.ENVIADO: "enviado_em",
        StatusOrcamentoAtacado.APROVADO: "aprovado_em",
        StatusOrcamentoAtacado.RECUSADO: "recusado_em",
        StatusOrcamentoAtacado.CANCELADO: "cancelado_em",
        StatusOrcamentoAtacado.EXPIRADO: "expirado_em",
        StatusOrcamentoAtacado.PEDIDO_GERADO: "pedido_gerado_em",
    }
    orcamento.status = destino
    update_fields = ["status", "atualizado_em"]
    campo_data = campos_data.get(destino)
    if campo_data:
        setattr(orcamento, campo_data, agora)
        update_fields.append(campo_data)
    orcamento.save(update_fields=update_fields)

    TransicaoOrcamentoAtacado.objects.create(
        orcamento=orcamento,
        status_origem=origem,
        status_destino=destino,
        usuario=usuario,
        observacao=observacao or "",
    )
    return orcamento


def expirar_orcamento_se_necessario(orcamento, *, usuario=None):
    if (
        orcamento.status == StatusOrcamentoAtacado.ENVIADO
        and orcamento.esta_expirado
    ):
        return transicionar_orcamento(
            orcamento,
            StatusOrcamentoAtacado.EXPIRADO,
            usuario=usuario,
            observacao="Expiração automática por validade.",
        )
    return orcamento


@transaction.atomic
def aprovar_orcamento_e_gerar_pedido(orcamento, *, usuario=None):
    """Aprovacao e pedido atomicos; serializa a operacao pelo orcamento."""
    from .order_services import gerar_pedido_de_orcamento_aprovado
    atual = OrcamentoAtacado.objects.select_for_update().get(pk=orcamento.pk)
    if atual.status != StatusOrcamentoAtacado.ENVIADO:
        raise ValidationError("Somente orçamento enviado pode ser aprovado e convertido em pedido.")
    transicionar_orcamento(
        atual, StatusOrcamentoAtacado.APROVADO,
        usuario=usuario, observacao="Orçamento aprovado para geração automática do pedido.",
    )
    return gerar_pedido_de_orcamento_aprovado(atual, usuario=usuario)
