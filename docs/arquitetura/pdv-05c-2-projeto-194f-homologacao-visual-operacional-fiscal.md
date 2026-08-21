# PDV-05C.2 — Projeto 194F — Homologação Visual e Operacional Fiscal

## 1. Objetivo

Criar um ponto de homologação humana para validar visual e operacionalmente
a fundação fiscal já construída.

A tela não será uma tela definitiva de emissão fiscal.

Ela será uma tela técnica/operacional de homologação ligada a uma venda já finalizada.

Fluxo alvo:

```text
Venda finalizada
    |
    v
Detalhe Fiscal
    |
    v
Snapshot fiscal
    |
    v
Preparar documento fiscal
    |
    v
DocumentoFiscal PREPARADO
    |
    v
Retry idempotente
```

---

## 2. Princípio arquitetural

Não alterar `finalizar_venda()`.

A homologação deve acontecer depois da venda estar finalizada.

Isso preserva a separação:

```text
fechamento comercial
!=
preparação documental
```

A indisponibilidade futura da SEFAZ não poderá bloquear o fechamento da venda.

---

## 3. Ponto de entrada

O ponto preferido é a venda já existente no histórico/detalhe.

A tela fiscal será vinculada por `venda_uuid`.

Fluxo:

```text
Histórico de vendas
    |
    v
Detalhe da venda
    |
    v
Ação "Fiscal"
    |
    v
Tela de homologação fiscal
```

Não criar um segundo histórico de vendas.

---

## 4. URL proposta

GET:

```text
/fiscal/homologacao/venda/<uuid:venda_uuid>/
```

Nome sugerido:

```text
fiscal:homologacao_documento_fiscal
```

POST de preparação:

```text
/fiscal/homologacao/venda/<uuid:venda_uuid>/preparar/
```

Nome sugerido:

```text
fiscal:preparar_documento_fiscal_homologacao
```

---

## 5. Permissões

A visualização deve exigir:

```text
login
+
PERMISSAO_PDV_VISUALIZAR
```

A ação de preparar deve exigir:

```text
login
+
PERMISSAO_PDV_OPERAR
```

Não criar permissão nova nesta sprint.

---

## 6. Escopo por matriz/loja

A view não deve usar `Venda.objects.get()` sem escopo.

Deve respeitar o mesmo isolamento já utilizado pelo PDV.

A venda precisa pertencer à matriz/loja acessível ao usuário.

---

## 7. Venda elegível

A tela pode ser aberta para qualquer venda visualizável.

Porém a ação de preparação somente estará disponível quando:

```text
venda finalizada
+
tipo_emissao == FISCAL
+
VendaFiscal existente
```

Venda não fiscal:

```text
somente leitura
+
mensagem "Venda não fiscal"
```

---

## 8. Snapshot fiscal

A tela deve mostrar claramente se existe:

```text
VendaFiscal
```

Status visual:

```text
Snapshot fiscal: OK
Snapshot fiscal: AUSENTE
```

Se ausente, a tela não deve tentar reconstruí-lo.

A homologação lê o snapshot histórico existente.

---

## 9. Dados de VendaFiscal

Mostrar:

```text
regime tributário
UF origem
UF destino
tipo de operação
finalidade
contribuinte ICMS
consumidor final
total base operação
total base ICMS
total ICMS
total FCP
total base PIS
total PIS
total base COFINS
total COFINS
total base IPI
total IPI
total tributos
resolvida em
```

---

## 10. Itens fiscais

Tabela de `ItemVendaFiscal`.

Colunas mínimas:

```text
Produto
NCM
CEST
CFOP
CST ICMS
CSOSN
CST PIS
CST COFINS
CST IPI
Quantidade
Valor unitário
Valor produtos
Base ICMS
Alíquota ICMS
ICMS
PIS
COFINS
IPI
Total tributos
```

A tela apenas exibe.

Não recalcular nenhum valor.

---

## 11. DocumentoFiscal

Se existir documento para a intenção de homologação, mostrar:

```text
UUID
modelo
ambiente
série
número
status
código status
motivo status
tentativa atual
chave de acesso, se existir
protocolo, se existir
criado em
atualizado em
```

A `idempotency_key` deve ser exibida truncada.

Exemplo:

```text
docfiscal:v1:3f92...a17c
```

Não mostrar chave completa por padrão.

---

## 12. Modelo da homologação

Primeira decisão para homologação:

```text
NFC-e modelo 65
```

Motivo:

- objetivo operacional é homologar fluxo de cupom fiscal;
- reduz escolhas na tela;
- não cria ainda regra automática definitiva de modelo.

A view não deve inferir permanentemente que toda venda será NFC-e.

Isso é apenas parâmetro de homologação.

---

## 13. Ambiente

Na tela de homologação:

```text
HOMOLOGACAO
```

fixo.

Não permitir PRODUCAO.

Produção só será liberada após provider real e credenciais.

---

## 14. Série

Para homologação operacional inicial:

```text
serie = 1
```

fixa na view/service de homologação.

Essa decisão é provisória e explícita.

Não espalhar `1` em múltiplos arquivos.

Definir uma constante local da camada de homologação.

---

## 15. Botão Preparar documento fiscal

Botão visível apenas quando:

```text
venda fiscal
+
snapshot existe
+
DocumentoFiscal inexistente ou em RASCUNHO/PREPARADO
```

Texto:

```text
Preparar documento fiscal
```

A ação deve chamar exclusivamente:

```python
preparar_documento_fiscal(...)
```

Nenhuma regra fiscal deve ser implementada na view.

---

## 16. Resultado de preparação

Após sucesso:

```text
Documento fiscal preparado com sucesso.
```

Redirecionar de volta para GET da homologação.

Pattern:

```text
POST
-> service
-> messages.success
-> redirect
```

Evitar refresh com reenvio de POST.

---

## 17. Retry

Se o documento já estiver `PREPARADO`:

clicar novamente deverá produzir:

```text
mesmo DocumentoFiscal
mesmo número
mesma idempotency_key
```

Mensagem:

```text
Documento fiscal já estava preparado.
```

A tela serve também para provar a idempotência.

---

## 18. Erros operacionais

Erros de `ValidationError` devem ser apresentados como mensagem legível.

Exemplos:

```text
Snapshot fiscal ausente.
Item fiscal sem NCM.
Item fiscal sem CFOP.
Documento fiscal em estado incompatível.
```

Não exibir traceback no navegador.

---

## 19. Estados

Badges sugeridos:

```text
RASCUNHO
PREPARADO
PENDENTE TRANSMISSÃO
TRANSMITINDO
AUTORIZADO
REJEITADO
DENEGADO
CONTINGÊNCIA
CANCELADO
ERRO
```

Porém nesta sprint a ação operacional termina em:

```text
PREPARADO
```

---

## 20. Proibições da interface

Não incluir:

```text
Autorizar
Transmitir
Cancelar SEFAZ
Gerar XML
Assinar XML
Gerar DANFE
Gerar QR Code
Produção
Upload de certificado
CSC/token
```

---

## 21. XML

Os campos:

```text
xml_rascunho
xml_assinado
xml_autorizado
```

não serão exibidos por padrão.

Podem ser indicados apenas como:

```text
XML rascunho: não disponível
XML assinado: não disponível
XML autorizado: não disponível
```

Sem conteúdo bruto.

---

## 22. Integração com detalhe da venda

Adicionar uma ação discreta no detalhe da venda:

```text
Fiscal
```

ou:

```text
Homologação fiscal
```

Preferência:

```text
Fiscal
```

Não alterar layout estrutural do PDV.

---

## 23. View GET

Responsabilidades:

```text
resolver venda com escopo
resolver VendaFiscal
resolver itens fiscais
resolver DocumentoFiscal existente
montar contexto
renderizar
```

Não pode:

```text
criar snapshot
preparar documento
recalcular tributos
reservar número
```

---

## 24. View POST

Responsabilidades:

```text
resolver venda com escopo
validar venda fiscal
obter VendaFiscal
chamar preparar_documento_fiscal
mensagem
redirect
```

Não deve manipular diretamente:

```text
DocumentoFiscal.objects.create()
SequenciaDocumentoFiscal
status
numero
idempotency_key
```

Tudo isso pertence aos services existentes.

---

## 25. Arquivos da Implementação 194G

Preferência:

```text
fiscal/views_homologacao.py
fiscal/templates/fiscal/homologacao_documento_fiscal.html
fiscal/tests/test_homologacao_documento_fiscal_ui.py
```

Alteração mínima:

```text
fiscal/urls.py
pdv/templates/pdv/detalhe_venda.html
```

Se `detalhe_venda.html` já for composto por partials, preferir alterar o partial correto.

---

## 26. Sem models/migrations

A Implementação 194G não deve criar:

```text
model
migration
campo novo
tabela nova
```

Tudo necessário já existe.

---

## 27. Testes de view

Cobertura mínima:

1. login obrigatório;
2. permissão de visualizar para GET;
3. permissão de operar para POST;
4. isolamento matriz/loja;
5. venda não fiscal não prepara;
6. venda fiscal sem snapshot não prepara;
7. snapshot aparece na tela;
8. itens fiscais aparecem;
9. botão aparece apenas quando permitido;
10. preparação chama o service;
11. sucesso redireciona;
12. retry reutiliza mesmo documento;
13. erro do service vira mensagem;
14. nenhuma ação AUTORIZAR existe.

---

## 28. Homologação visual manual

Após Implementação 194G:

### Passo A

Abrir:

```text
PDV -> Histórico de vendas -> Detalhe
```

Confirmar botão:

```text
Fiscal
```

### Passo B

Abrir tela fiscal.

Confirmar:

```text
identificação da venda
snapshot
itens
totais
```

### Passo C

Antes de preparar:

```text
Documento fiscal: ainda não preparado
```

### Passo D

Clicar:

```text
Preparar documento fiscal
```

Confirmar:

```text
status PREPARADO
modelo 65
ambiente HOMOLOGACAO
serie 1
numero preenchido
```

### Passo E

Anotar número.

Clicar novamente.

Confirmar:

```text
mesmo UUID
mesmo número
mesma intenção
```

---

## 29. Homologação operacional

Além da aparência, validar no banco através da própria UI:

```text
1 VendaFiscal por venda
N ItemVendaFiscal esperados
1 DocumentoFiscal para a intenção
numero reservado uma única vez
status PREPARADO
```

---

## 30. Gate para retomar provider

Somente retomar Projeto 195 quando o usuário confirmar visualmente:

```text
[ ] consigo abrir a tela fiscal
[ ] vejo snapshot
[ ] vejo itens fiscais
[ ] vejo totais
[ ] consigo preparar
[ ] vejo PREPARADO
[ ] vejo número
[ ] retry mantém número
[ ] nenhuma duplicidade visual
[ ] nenhuma regressão no detalhe da venda
```

---

## 31. Fluxo final desta etapa

```text
Histórico de vendas
        |
        v
Detalhe da venda
        |
        v
Fiscal
        |
        v
Homologação Fiscal
        |
        +--> Snapshot da venda
        |
        +--> Itens fiscais
        |
        +--> DocumentoFiscal
        |
        +--> Preparar
                 |
                 v
            PREPARADO
                 |
                 v
              Retry
                 |
                 v
        mesmo documento/número
```

---

## 32. Fora do escopo

Continuam fora:

```text
provider
SEFAZ
HTTP
XML oficial
assinatura digital
certificado A1
CSC
QR Code
DANFE
autorização
cancelamento externo
produção
```

---

## 33. Próximo passo

Após validação deste contrato:

```text
Implementação 194G
```

Objetivo:

> disponibilizar homologação humana real das implementações fiscais já construídas.