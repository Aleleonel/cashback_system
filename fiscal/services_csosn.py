from django.core.exceptions import ValidationError
from django.db import transaction
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CSOSN

def _validar(codigo, descricao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}
    if len(codigo) != 3 or not codigo.isdigit():
        erros["codigo"] = "Informe exatamente tres digitos."
    if not descricao:
        erros["descricao"] = "Informe a descricao do CSOSN."
    qs = CSOSN.objects.filter(codigo=codigo)
    if excluido is not None:
        qs = qs.exclude(id=excluido.id)
    if codigo and qs.exists():
        erros["codigo"] = "Ja existe um CSOSN com este codigo."
    if erros:
        raise ValidationError(erros)
    return codigo, descricao

def _auditar(csosn, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(usuario=usuario, matriz=matriz, loja=loja, acao=acao, recurso="fiscal.csosn", recurso_id=csosn.id, descricao=descricao, request=request)

@transaction.atomic
def criar_csosn(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(dados.get("codigo"), dados.get("descricao"))
    csosn = CSOSN(codigo=codigo, descricao=descricao, exige_aliquota=dados.get("exige_aliquota", False), permite_reducao_base=dados.get("permite_reducao_base", False), permite_credito=dados.get("permite_credito", False), permite_substituicao_tributaria=dados.get("permite_substituicao_tributaria", False), ativo=dados.get("ativo", True))
    csosn.save()
    _auditar(csosn, usuario_executor, matriz, loja, request, RegistroAuditoria.ACAO_CRIAR, f"CSOSN criado: {csosn}")
    return csosn

@transaction.atomic
def editar_csosn(*, csosn, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(csosn.codigo, dados.get("descricao"), csosn)
    csosn.codigo = codigo
    csosn.descricao = descricao
    csosn.exige_aliquota = dados.get("exige_aliquota", csosn.exige_aliquota)
    csosn.permite_reducao_base = dados.get("permite_reducao_base", csosn.permite_reducao_base)
    csosn.permite_credito = dados.get("permite_credito", csosn.permite_credito)
    csosn.permite_substituicao_tributaria = dados.get("permite_substituicao_tributaria", csosn.permite_substituicao_tributaria)
    csosn.ativo = dados.get("ativo", csosn.ativo)
    csosn.save()
    _auditar(csosn, usuario_executor, matriz, loja, request, RegistroAuditoria.ACAO_EDITAR, f"CSOSN atualizado: {csosn}")
    return csosn
