"""Interface de conciliação manual, com escopo e autorização explícitos."""
import uuid
from decimal import Decimal
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from pdv.models import PagamentoVenda
from financeiro.models import BaixaFinanceira
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR, PERMISSAO_FINANCEIRO_GERENCIAR
from financeiro.conciliacao_adquirente import registrar_repasse_adquirente, estornar_repasse_adquirente
from financeiro.models import BaixaFinanceira, ContaFinanceira, ParcelaFinanceira, PlanoConta, TituloFinanceiro
from pdv.models import FormaPagamento
from pdv.choices import TipoFormaPagamento
from .views import _matriz_usuario, _lojas_autorizadas

class RecebivelCartaoChoiceField(forms.ModelChoiceField):
    """Descrição operacional local ao formulário, sem modificar __str__ do modelo."""
    def label_from_instance(self, parcela):
        titulo = parcela.titulo
        valor = f'{parcela.valor_original:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
        return f'Título #{titulo.pk} · Parcela {parcela.numero} · R$ {valor}'

class RepasseForm(forms.Form):
    parcela = RecebivelCartaoChoiceField(queryset=ParcelaFinanceira.objects.none(), label='Recebível de cartão')
    forma_pagamento = forms.ModelChoiceField(queryset=FormaPagamento.objects.none(), label='Forma de pagamento original')
    conta_financeira = forms.ModelChoiceField(queryset=ContaFinanceira.objects.none(), label='Conta bancária de destino')
    plano_taxas = forms.ModelChoiceField(queryset=PlanoConta.objects.none(), required=False, label='Plano de despesa da taxa')
    bruto = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'), label='Valor bruto (R$)')
    taxa = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.00'), initial=0, label='Taxa (R$)')
    data = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}, format='%Y-%m-%d'), label='Data do repasse')
    observacao = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={'rows':2}), label='Observações')

    def __init__(self, *args, matriz, lojas, **kwargs):
        super().__init__(*args, **kwargs)
        loja_ids = list(lojas.values_list('pk', flat=True))
        # Elegibilidade demonstrada pela origem da venda, nao apenas pelo tipo do titulo.
        candidatos = list(ParcelaFinanceira.objects.filter(
            titulo__matriz=matriz, titulo__loja_id__in=loja_ids,
            titulo__natureza=TituloFinanceiro.Natureza.RECEBER,
            titulo__origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            status__in=[ParcelaFinanceira.Status.ABERTO, ParcelaFinanceira.Status.PARCIAL],
        ).select_related('titulo').order_by('-pk')[:1000])
        origens = set()
        for p in candidatos:
            try:
                origens.add(str(uuid.UUID(str(p.titulo.origem_id))))
            except (ValueError, TypeError, AttributeError):
                continue
        pagamentos = {
            str(pg.uuid): pg for pg in PagamentoVenda.objects.filter(
                uuid__in=origens, venda__matriz=matriz, venda__loja_id__in=loja_ids,
                forma_pagamento__matriz=matriz, forma_pagamento__ativa=True,
                forma_pagamento__tipo__in=[TipoFormaPagamento.CARTAO_CREDITO, TipoFormaPagamento.CARTAO_DEBITO],
            ).select_related('venda__cliente', 'forma_pagamento')
        }
        self.pagamentos_elegiveis = {}
        self.saldos_elegiveis = {}
        ids = []
        for parcela in candidatos:
            titulo = parcela.titulo
            pg = pagamentos.get(str(titulo.origem_id))
            if not pg or titulo.chave_idempotencia != f'venda-pagamento:{pg.uuid}':
                continue
            totais = {row['tipo']: row['total'] for row in
                BaixaFinanceira.objects.filter(parcela=parcela).values('tipo').annotate(total=Sum('valor'))}
            saldo = (parcela.valor_original
                     - (totais.get(BaixaFinanceira.Tipo.BAIXA) or Decimal('0'))
                     + (totais.get(BaixaFinanceira.Tipo.ESTORNO) or Decimal('0')))
            if saldo <= 0:
                continue
            ids.append(parcela.pk)
            self.pagamentos_elegiveis[parcela.pk] = pg
            self.saldos_elegiveis[parcela.pk] = saldo
            if len(ids) >= 250:
                break
        self.fields['parcela'].queryset = ParcelaFinanceira.objects.filter(pk__in=ids).select_related('titulo').order_by('-pk')
        self.fields['forma_pagamento'].queryset = FormaPagamento.objects.filter(
            matriz=matriz, ativa=True, tipo__in=[TipoFormaPagamento.CARTAO_CREDITO, TipoFormaPagamento.CARTAO_DEBITO])
        self.fields['conta_financeira'].queryset = ContaFinanceira.objects.filter(
            matriz=matriz, ativo=True).filter(Q(loja__isnull=True)|Q(loja_id__in=loja_ids))
        self.fields['plano_taxas'].queryset = PlanoConta.objects.filter(
            matriz=matriz, ativo=True, tipo=PlanoConta.Tipo.ANALITICA,
            natureza=PlanoConta.Natureza.DESPESA, aceita_lancamento=True,
            classificacao_dre=PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field, forms.ModelChoiceField) else 'form-control'

    def clean(self):
        dados=super().clean()
        bruto, taxa = dados.get('bruto'), dados.get('taxa')
        if bruto is not None and taxa is not None and taxa >= bruto:
            self.add_error('taxa','A taxa deve ser inferior ao bruto.')
        if taxa and not dados.get('plano_taxas'):
            self.add_error('plano_taxas','Informe o plano de despesa financeira.')
        parcela, conta = dados.get('parcela'), dados.get('conta_financeira')
        if parcela:
            pg = self.pagamentos_elegiveis.get(parcela.pk)
            if pg is None:
                self.add_error('parcela', 'Recebivel sem origem comprovada em cartao.')
            elif dados.get('forma_pagamento') and dados['forma_pagamento'].pk != pg.forma_pagamento_id:
                self.add_error('forma_pagamento', 'Selecione a forma de pagamento original da venda.')
            if bruto is not None and bruto > self.saldos_elegiveis.get(parcela.pk, Decimal('0')):
                self.add_error('bruto', 'O bruto excede o saldo disponivel da parcela.')
        if parcela and conta and conta.loja_id and conta.loja_id != parcela.titulo.loja_id:
            self.add_error('conta_financeira','A conta pertence a outra loja.')
        return dados

class EstornoRepasseForm(forms.Form):
    data = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}, format='%Y-%m-%d'), label='Data do estorno')
    confirmar = forms.BooleanField(label='Confirmo o estorno integral da baixa e da taxa associada')
    motivo = forms.CharField(min_length=11, max_length=500, label='Justificativa obrigatoria', widget=forms.Textarea(attrs={'rows': 3}))


def _erros(form, exc):
    if hasattr(exc, 'message_dict'):
        for campo, mensagens in exc.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in exc.messages:
            form.add_error(None, mensagem)

@login_required
@require_permission(PERMISSAO_FINANCEIRO_BAIXAR)
def repasse_novo(request):
    matriz=_matriz_usuario(request)
    lojas=_lojas_autorizadas(request, matriz)
    if not lojas.exists():
        raise Http404('Nenhuma loja autorizada.')
    form=RepasseForm(request.POST if request.method=='POST' else None,
                     initial={'data':timezone.localdate()}, matriz=matriz, lojas=lojas)
    if request.method=='POST' and form.is_valid():
        try:
            token=str(uuid.UUID(request.POST.get('chave_idempotencia','')))
        except (ValueError, TypeError, AttributeError):
            form.add_error(None,'Identificador de operação inválido. Recarregue o formulário.')
        else:
            dados=form.cleaned_data
            try:
                registrar_repasse_adquirente(
                    parcela=dados['parcela'], bruto=dados['bruto'], taxa=dados['taxa'],
                    data=dados['data'], chave_idempotencia=f'ui:{matriz.pk}:{token}',
                    forma_pagamento=dados['forma_pagamento'], conta_financeira=dados['conta_financeira'],
                    plano_taxas=dados['plano_taxas'], observacao=dados['observacao'],
                    usuario=request.user, request=request)
            except ValidationError as exc:
                _erros(form,exc)
            else:
                return redirect('financeiro:titulo_detalhe', titulo_uuid=dados['parcela'].titulo.uuid)
    token=request.POST.get('chave_idempotencia') if request.method=='POST' else str(uuid.uuid4())
    detalhes = {}
    for parcela in form.fields['parcela'].queryset:
        titulo = parcela.titulo
        pagamento = form.pagamentos_elegiveis[parcela.pk]
        cliente = pagamento.venda.cliente
        detalhes[str(parcela.pk)] = {
            'titulo': str(titulo.pk), 'parcela': str(parcela.numero),
            'cliente': str(cliente) if cliente else 'Consumidor nao identificado',
            'loja': str(titulo.loja) if titulo.loja_id else 'Sem loja',
            'forma': str(pagamento.forma_pagamento),
            'forma_id': pagamento.forma_pagamento_id,
            'original': str(parcela.valor_original),
            'saldo': str(form.saldos_elegiveis[parcela.pk]),
            'status': parcela.get_status_display(),
            'vencimento': parcela.vencimento.strftime('%d/%m/%Y'),
        }
    return render(request,'financeiro/repasse_form.html',{
        'form':form,'chave_idempotencia':token,'detalhes_recebiveis':detalhes})

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def repasse_estornar(request, baixa_id):
    matriz=_matriz_usuario(request)
    lojas=_lojas_autorizadas(request,matriz)
    baixa=get_object_or_404(BaixaFinanceira.objects.select_related('parcela__titulo'),
        pk=baixa_id, parcela__titulo__matriz=matriz,
        parcela__titulo__loja_id__in=lojas.values_list('pk',flat=True),
        tipo=BaixaFinanceira.Tipo.BAIXA)
    if not baixa.chave_idempotencia.startswith('adquirente:') or not baixa.chave_idempotencia.endswith(':bruto'):
        raise Http404('Baixa não corresponde a um repasse conciliado.')
    form=EstornoRepasseForm(request.POST if request.method=='POST' else None,initial={'data':timezone.localdate()})
    if request.method=='POST' and form.is_valid():
        try:
            token=str(uuid.UUID(request.POST.get('chave_idempotencia','')))
        except (ValueError,TypeError,AttributeError):
            form.add_error(None,'Identificador de estorno inválido.')
        else:
            try:
                estornar_repasse_adquirente(baixa=baixa,data=form.cleaned_data['data'],
                    chave_idempotencia=f'ui:{matriz.pk}:{token}',motivo=form.cleaned_data['motivo'],usuario=request.user,request=request)
            except ValidationError as exc:
                _erros(form,exc)
            else:
                return redirect('financeiro:titulo_detalhe',titulo_uuid=baixa.parcela.titulo.uuid)
    token=request.POST.get('chave_idempotencia') if request.method=='POST' else str(uuid.uuid4())
    return render(request,'financeiro/repasse_estorno.html',{'form':form,'baixa':baixa,'chave_idempotencia':token})
