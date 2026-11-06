from decimal import Decimal
from html import escape
from django.utils import timezone
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _texto(obj, atributo, padrao="-"):
    valor = getattr(obj, atributo, None)
    return padrao if valor in (None, "") else str(valor)


def _nome_relacionado(obj, atributo):
    valor = getattr(obj, atributo, None)
    if valor is None:
        return "-"
    return str(valor)


def _itens(obj):
    # Descobre o related manager sem depender de related_name customizado.
    for rel in obj._meta.related_objects:
        model = rel.related_model
        if model.__name__ in {"ItemOrcamentoAtacado", "ItemPedidoAtacado"}:
            return getattr(obj, rel.get_accessor_name()).all()
    return []


def _linha_item(item, pedido=False):
    percentual = getattr(item, "percentual_desconto", None) if pedido else getattr(item, "percentual_desconto_atacado", None)
    promocional = getattr(item, "produto_promocional_snapshot", None) if pedido else getattr(item, "produto_promocional", None)
    justificativa = getattr(item, "justificativa_negociacao_snapshot", "") if pedido else getattr(item, "justificativa_negociacao", "")
    return [
        _nome_relacionado(item, "produto"),
        item.quantidade,
        item.preco_unitario_original,
        item.preco_unitario_base,
        item.preco_unitario_final,
        percentual or 0,
        item.desconto_atacado,
        item.ajuste_negociado,
        "Sim" if promocional else "Nao",
        justificativa or "",
    ]


def _dados_documento(obj, pedido=False):
    numero = getattr(obj, "numero", None)
    if pedido and numero is None:
        numero = getattr(obj, "pk", None)
    validade = getattr(obj, "valido_ate", None)
    observacoes = getattr(obj, "observacoes_snapshot", "") if pedido else getattr(obj, "observacoes", "")
    return {
        "titulo": "Pedido de Atacado" if pedido else "Orcamento de Atacado",
        "numero": numero or getattr(obj, "pk", "-"),
        "cliente": _nome_relacionado(obj, "cliente"),
        "vendedor": _nome_relacionado(obj, "vendedor"),
        "validade": validade or "-",
        "observacoes": observacoes or "",
        "subtotal": obj.subtotal_produtos,
        "desconto": obj.desconto_atacado,
        "ajustes": obj.ajustes_negociados,
        "frete": obj.frete,
        "total": obj.total,
        "itens": [_linha_item(i, pedido=pedido) for i in _itens(obj)],
    }


# F32M5P2_LAYOUT_PDF - apresentacao comercial, sem alterar XLSX nem dados.
def _pdf_fontes():
    import os
    candidatos = [
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for regular, negrito in candidatos:
        if os.path.isfile(regular) and os.path.isfile(negrito):
            try:
                if "F32PDFRegular" not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont("F32PDFRegular", regular))
                if "F32PDFBold" not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont("F32PDFBold", negrito))
                return "F32PDFRegular", "F32PDFBold"
            except Exception:
                continue
    return "Helvetica", "Helvetica-Bold"


def _pdf_moeda(valor):
    try:
        numero = Decimal(str(valor or 0))
        s = f"{numero:,.2f}"
        return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return "R$ 0,00"


def _pdf_numero(valor, casas=2):
    try:
        s = f"{Decimal(str(valor or 0)):,.{casas}f}"
        return s.replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return "-"


def _pdf_data(valor):
    if not valor or valor == "-":
        return "Nao informada"
    if hasattr(valor, "tzinfo"):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.strftime("%d/%m/%Y")
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _gerar_pdf(obj, pedido=False):
    """F32M5P8B: layout comercial compacto baseado no modelo aprovado."""
    d = _dados_documento(obj, pedido=pedido)
    normal, bold = _pdf_fontes()
    preto = HexColor('#222222')
    borda = HexColor('#B8B8B8')
    faixa = HexColor('#E6E6E6')
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28,
                            topMargin=25, bottomMargin=38, title=d['titulo'])
    largura = A4[0] - 56
    estilo = ParagraphStyle('P8Texto', fontName=normal, fontSize=7.4, leading=10, textColor=preto)
    pequeno = ParagraphStyle('P8Pequeno', parent=estilo, fontSize=6.8, leading=9)
    negrito = ParagraphStyle('P8Negrito', parent=estilo, fontName=bold)
    centro = ParagraphStyle('P8Centro', parent=negrito, alignment=1, fontSize=10, leading=13)
    direita = ParagraphStyle('P8Direita', parent=estilo, alignment=TA_RIGHT)
    def P(v, s=estilo):
        return Paragraph(escape(str(v if v is not None else '')), s)
    def txt(o, campo):
        return str(getattr(o, campo, '') or '').strip() if o is not None else ''
    def money(v):
        return _pdf_moeda(v)
    def tabela(celulas, larguras, estilos=None, repetir=0):
        t = Table(celulas, colWidths=larguras, hAlign='LEFT', repeatRows=repetir)
        base = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]
        t.setStyle(TableStyle(base + (estilos or [])))
        return t
    def titulo_secao(nome):
        return tabela([[P(nome, negrito)]], [largura],
                      [('BACKGROUND',(0,0),(-1,-1),faixa),('BOX',(0,0),(-1,-1),.5,borda)])
    story = []
    loja = getattr(obj, 'loja', None)
    cfg = None
    if loja is not None and getattr(loja, 'pk', None):
        from fiscal.models import ConfiguracaoEmissaoFiscalLoja
        cfg = ConfiguracaoEmissaoFiscalLoja.objects.filter(loja_id=loja.pk).first()
    nome = txt(cfg, 'nome_fantasia') or txt(loja, 'nome') or txt(cfg, 'razao_social') or 'EMPRESA NAO CADASTRADA'
    razao = txt(cfg, 'razao_social')
    cnpj = txt(loja, 'cnpj')
    ie = txt(cfg, 'inscricao_estadual')
    endereco = ', '.join(x for x in (txt(cfg,'logradouro'),txt(cfg,'numero')) if x)
    if txt(cfg,'complemento'):
        endereco += ' - ' + txt(cfg,'complemento')
    local = ' / '.join(x for x in (txt(cfg,'municipio'),txt(cfg,'uf')) if x)
    end2 = ' - '.join(x for x in (txt(cfg,'bairro'),local) if x)
    cep = txt(cfg,'cep')
    telefone = txt(loja,'telefone')
    vendedor = d['vendedor']
    esquerda = [P(nome, negrito)]
    if razao and razao != nome: esquerda.append(P('Razao social: ' + razao, pequeno))
    esquerda.extend([P('CNPJ: ' + (cnpj or 'Nao cadastrado') + ('   IE: ' + ie if ie else ''), pequeno),
                     P(endereco or 'Endereco nao cadastrado', pequeno),
                     P(end2 + (' - CEP: ' + cep if cep else ''), pequeno)])
    direita_em = [P('Telefone: ' + (telefone or 'Nao cadastrado'), pequeno),
                  P('Vendedor: ' + str(vendedor), pequeno)]
    cab = tabela([[esquerda, direita_em]], [largura*.66, largura*.34],
                 [('BOX',(0,0),(-1,-1),.6,borda),('TOPPADDING',(0,0),(-1,-1),7),
                  ('BOTTOMPADDING',(0,0),(-1,-1),7)])
    story.extend([cab, Spacer(1,7)])
    emissao = getattr(obj,'criado_em',None)
    if emissao is not None and timezone.is_aware(emissao):
        emissao = timezone.localtime(emissao)
    nome_doc = 'PEDIDO' if pedido else 'ORCAMENTO'
    faixa_doc = tabela([[P(nome_doc + ' Nº ' + str(d['numero']), centro), P(_pdf_data(emissao), direita)]],
                       [largura*.77, largura*.23],
                       [('BACKGROUND',(0,0),(-1,-1),faixa),('BOX',(0,0),(-1,-1),.5,borda)])
    story.extend([faixa_doc, Spacer(1,5)])
    if not pedido and d['validade'] != '-':
        story.extend([tabela([[P('VALIDADE DA PROPOSTA: ' + _pdf_data(d['validade']), negrito)]],
                             [largura], [('BACKGROUND',(0,0),(-1,-1),faixa),
                                         ('BOX',(0,0),(-1,-1),.5,borda)]), Spacer(1,6)])
    cliente = getattr(obj,'cliente',None)
    pf = not bool(txt(cliente,'cnpj'))
    nome_cli = txt(cliente,'nome') if pf else (txt(cliente,'razao_social') or txt(cliente,'nome'))
    fantasia_cli = txt(cliente,'nome_fantasia')
    doc_cli = txt(cliente,'cpf') if pf else txt(cliente,'cnpj')
    end_cli = ', '.join(x for x in (txt(cliente,'logradouro'),txt(cliente,'numero')) if x)
    if txt(cliente,'complemento'): end_cli += ' - ' + txt(cliente,'complemento')
    if txt(cliente,'bairro'): end_cli += ' - ' + txt(cliente,'bairro')
    local_cli = '/'.join(x for x in (txt(cliente,'cidade'),txt(cliente,'uf')) if x)
    pares = [
        ('Nome / Razao social:', nome_cli, 'Nome fantasia:', fantasia_cli),
        ('CNPJ / CPF:', doc_cli, 'Endereco:', end_cli),
        ('CEP:', txt(cliente,'cep'), 'Cidade / UF:', local_cli),
        ('Telefone:', txt(cliente,'telefone'), 'E-mail:', txt(cliente,'email')),
    ]
    if not pf and txt(cliente,'inscricao_estadual'):
        pares.append(('Inscricao estadual:', txt(cliente,'inscricao_estadual'), 'Contato:', txt(cliente,'contato_responsavel')))
    elif txt(cliente,'contato_responsavel'):
        pares.append(('Contato:', txt(cliente,'contato_responsavel'), '', ''))
    dados_cliente = [[P(a, negrito), P(b, pequeno), P(c, negrito), P(e, pequeno)] for a,b,c,e in pares]
    story.extend([titulo_secao('DADOS DO CLIENTE'),
                  tabela(dados_cliente,[largura*.19,largura*.31,largura*.17,largura*.33],
                         [('GRID',(0,0),(-1,-1),.4,borda)]), Spacer(1,7)])
    story.append(titulo_secao('PRODUTOS'))
    colunas = [largura*x for x in (.055,.405,.075,.105,.125,.105,.13)]
    linhas = [[P('ITEM',negrito),P('NOME',negrito),P('UND.',negrito),
               P('QTD.',negrito),P('VR. UNIT.',negrito),P('DESC.',negrito),P('SUBTOTAL',negrito)]]
    total_qtd = Decimal('0')
    subtotal_linhas = Decimal('0')
    itens_origem = list(_itens(obj))
    if len(itens_origem) != len(d['itens']):
        raise ValueError('Itens de origem e exportacao divergentes')
    for n,item in enumerate(d['itens'],1):
        produto,qtd,original,base,final,pct,desc,ajuste,promo,justificativa = item
        try: subtotal_item = Decimal(str(qtd))*Decimal(str(final))
        except Exception: subtotal_item = Decimal('0')
        subtotal_linhas += subtotal_item
        produto_origem = getattr(itens_origem[n-1], 'produto', None)
        unidade = getattr(produto_origem, 'unidade_medida', None)
        sigla_unidade = str(getattr(unidade, 'sigla', '') or '').strip()
        if not sigla_unidade:
            sigla_unidade = 'N/I'
        try: total_qtd += Decimal(str(qtd))
        except Exception: pass
        detalhe = []
        if promo == 'Sim': detalhe.append('Promocional')
        if ajuste and Decimal(str(ajuste)) != 0: detalhe.append('Ajuste: '+money(ajuste))
        if justificativa: detalhe.append('Obs.: '+str(justificativa))
        nome_prod = escape(str(produto))
        if detalhe: nome_prod += '<br/><font size="6">'+escape(' | '.join(detalhe))+'</font>'
        linhas.append([P(n,pequeno),Paragraph(nome_prod,pequeno),P(sigla_unidade,pequeno),
                       P(_pdf_numero(qtd,2),direita),P(_pdf_numero(original),direita),
                       P(_pdf_numero(pct)+'%',direita),P(_pdf_numero(subtotal_item),direita)])
    if len(linhas)==1: linhas.append(['',P('Nenhum produto cadastrado',pequeno),'','','','',''])
    linhas.append([P('TOTAL',negrito),'','',P(_pdf_numero(total_qtd,2),direita),'','',P(_pdf_numero(subtotal_linhas),direita)])
    tbl_prod = tabela(linhas,colunas,[('GRID',(0,0),(-1,-1),.4,borda),
                                      ('BACKGROUND',(0,0),(-1,0),faixa),
                                      ('BACKGROUND',(0,-1),(-1,-1),faixa),
                                      ('SPAN',(0,-1),(1,-1))],repetir=1)
    story.extend([tbl_prod,Spacer(1,7)])
    resumo = [
        [P('SUBTOTAL DOS PRODUTOS:',negrito),P(money(d['subtotal']),direita)],
        [P('DESCONTO ATACADISTA:',negrito),P('- '+money(d['desconto']),direita)],
        [P('AJUSTES NEGOCIADOS:',negrito),P(money(d['ajustes']),direita)],
        [P('FRETE:',negrito),P(money(d['frete']),direita)],
        [P('TOTAL: ',negrito),P(money(d['total']),direita)],
    ]
    totais = tabela(resumo,[largura*.75,largura*.25],
                    [('BOX',(0,0),(-1,-1),.5,borda),('LINEABOVE',(0,-1),(-1,-1),.6,borda),
                     ('BACKGROUND',(0,-1),(-1,-1),faixa)])
    story.extend([totais,Spacer(1,8)])
    if not pedido:
        forma = getattr(obj,'forma_pagamento',None)
        parcelas = getattr(obj,'parcelas',1) or 1
        cond = str(forma) + ' - ' + str(parcelas) + (' parcela' if parcelas==1 else ' parcelas') if forma else 'A definir'
        story.extend([P('Condicoes de pagamento: '+cond,pequeno),Spacer(1,5)])
    if d['observacoes']:
        story.extend([P('OBSERVACOES:',negrito),P(d['observacoes'],pequeno),Spacer(1,7)])
    assinatura = tabela([[P('_______________________________________________',centro)],
                        [P('Assinatura do cliente',centro)]],[largura],
                       [('BOX',(0,0),(-1,-1),.7,borda),('TOPPADDING',(0,0),(-1,0),12),
                        ('BOTTOMPADDING',(0,-1),(-1,-1),9)])
    story.append(assinatura)
    def rodape(canvas, documento):
        canvas.saveState()
        canvas.setFont(normal,6.5)
        canvas.setFillColor(preto)
        canvas.drawString(28,22,'Documento comercial - PRO Cash')
        canvas.drawRightString(A4[0]-28,22,'Pagina '+str(documento.page))
        canvas.restoreState()
    doc.build(story,onFirstPage=rodape,onLaterPages=rodape)
    return buffer.getvalue()


def _gerar_xlsx(obj, pedido=False):
    d = _dados_documento(obj, pedido=pedido)
    wb = Workbook()
    ws = wb.active
    ws.title = "Pedido Atacado" if pedido else "Orcamento Atacado"
    ws.append([d["titulo"]])
    ws.append(["Numero", d["numero"]])
    ws.append(["Cliente", d["cliente"]])
    ws.append(["Vendedor", d["vendedor"]])
    ws.append(["Validade", _pdf_data(d["validade"]) if d["validade"] != "-" else "-"])
    ws.append([])
    ws.append(["Produto", "Quantidade", "Preco original", "Preco base", "Preco final", "% atacado", "Desconto", "Ajuste", "Promocional", "Justificativa"])
    for linha in d["itens"]:
        ws.append(linha)
    ws.append([])
    ws.append(["Subtotal produtos", d["subtotal"]])
    ws.append(["Desconto atacado", d["desconto"]])
    ws.append(["Ajustes negociados", d["ajustes"]])
    ws.append(["Frete", d["frete"]])
    ws.append(["Total", d["total"]])
    ws.append(["Observacoes", d["observacoes"]])
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def exportar_orcamento_pdf(orcamento):
    return _gerar_pdf(orcamento, pedido=False)


def exportar_orcamento_xlsx(orcamento):
    return _gerar_xlsx(orcamento, pedido=False)


def exportar_pedido_pdf(pedido):
    return _gerar_pdf(pedido, pedido=True)


def exportar_pedido_xlsx(pedido):
    return _gerar_xlsx(pedido, pedido=True)
