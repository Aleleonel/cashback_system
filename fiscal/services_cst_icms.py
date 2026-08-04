from django.core.exceptions import ValidationError
from django.db import transaction
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from fiscal.models import CSTICMS

def _validar(codigo, descricao, excluido=None):
    codigo = (codigo or "").strip()
    descricao = (descricao or "").strip()
    erros = {}
    if len(codigo) != 2 or not codigo.isdigit():
        erros["codigo"] = "Informe exatamente dois digitos."
    if not descricao:
        erros["descricao"] = "Informe a descricao do CST ICMS."
    qs = CSTICMS.objects.filter(codigo=codigo)
    if excluido is not None:
        qs = qs.exclude(id=excluido.id)
    if codigo and qs.exists():
        erros["codigo"] = "Ja existe um CST ICMS com este codigo."
    if erros:
        raise ValidationError(erros)
    return codigo, descricao

def _auditar(cst, usuario, matriz, loja, request, acao, descricao):
    registrar_auditoria(usuario=usuario, matriz=matriz, loja=loja, acao=acao, recurso="fiscal.cst_icms", recurso_id=cst.id, descricao=descricao, request=request)

@transaction.atomic
def criar_cst_icms(*, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(dados.get("codigo"), dados.get("descricao"))
    cst = CSTICMS(codigo=codigo, descricao=descricao, exige_aliquota=dados.get("exige_aliquota", False), permite_reducao_base=dados.get("permite_reducao_base", False), permite_diferimento=dados.get("permite_diferimento", False), permite_substituicao_tributaria=dados.get("permite_substituicao_tributaria", False), ativo=dados.get("ativo", True))
    cst.save()
    _auditar(cst, usuario_executor, matriz, loja, request, RegistroAuditoria.ACAO_CRIAR, f"CST ICMS criado: {cst}")
    return cst

@transaction.atomic
def editar_cst_icms(*, cst, dados, usuario_executor, matriz, loja=None, request=None):
    codigo, descricao = _validar(cst.codigo, dados.get("descricao"), cst)
    cst.codigo = codigo
    cst.descricao = descricao
    cst.exige_aliquota = dados.get("exige_aliquota", cst.exige_aliquota)
    cst.permite_reducao_base = dados.get("permite_reducao_base", cst.permite_reducao_base)
    cst.permite_diferimento = dados.get("permite_diferimento", cst.permite_diferimento)
    cst.permite_substituicao_tributaria = dados.get("permite_substituicao_tributaria", cst.permite_substituicao_tributaria)
    cst.ativo = dados.get("ativo", cst.ativo)
    cst.save()
    _auditar(cst, usuario_executor, matriz, loja, request, RegistroAuditoria.ACAO_EDITAR, f"CST ICMS atualizado: {cst}")
    return cst
