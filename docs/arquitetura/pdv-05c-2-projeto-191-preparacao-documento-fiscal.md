# PDV-05C.2 — Projeto 191 — Contrato de Preparação do Documento Fiscal

## 1. Objetivo

Definir o fluxo interno que transforma o snapshot fiscal histórico da venda em um `DocumentoFiscal` apto a entrar no estado `PREPARADO`.

Esta etapa não gera XML oficial, não assina documento, não transmite à SEFAZ e não cria DANFE.

A origem oficial dos dados continua sendo:

```text
VendaFiscal
+
ItemVendaFiscal
```

O destino desta etapa será:

```text
DocumentoFiscal
status = RASCUNHO
        |
        v
status = PREPARADO
```

---

## 2. Regra principal

A preparação do Documento Fiscal deve ser determinística, idempotente e local.

Fluxo conceitual:

```text
VendaFiscal
  |
  +--> validar elegibilidade
  |
  +--> definir modelo
  |
  +--> definir ambiente
  |
  +--> definir serie
  |
  +--> criar/recuperar DocumentoFiscal RASCUNHO
  |
  +--> construir payload interno
  |
  +--> validar campos obrigatorios
  |
  +--> reservar numero, quando realmente necessario
  |
  +--> transicionar para PREPARADO
```

Nenhuma chamada externa deve acontecer nesse fluxo.

---

## 3. Origem dos dados

O `DocumentoFiscal` não deve ler regras fiscais diretamente de produto ou cadastro operacional.

A origem fiscal deve ser exclusivamente o snapshot:

```text
VendaFiscal
ItemVendaFiscal
```

Isso preserva consistência histórica.

Se o produto ou regra fiscal mudar depois da venda, o documento continua baseado no snapshot congelado.

---

## 4. Serviço de preparação

A futura implementação deverá expor um serviço semelhante a:

```python
preparar_documento_fiscal(
    *,
    venda_fiscal,
    modelo,
    ambiente,
    serie,
)
```

Esse serviço deve:

1. validar o snapshot;
2. localizar ou criar o DocumentoFiscal idempotente;
3. construir DTO/payload interno;
4. validar completude;
5. decidir se a numeração deve ser reservada;
6. transicionar para `PREPARADO`.

---

## 5. Criação idempotente

Não usar `create()` diretamente sem estratégia de idempotência.

Fluxo conceitual:

```text
idempotency_key
=
venda_fiscal
+ modelo
+ ambiente
+ serie
+ intencao_emissao
```

Primeira chamada:

```text
cria DocumentoFiscal
```

Chamadas repetidas com mesma intenção:

```text
retornam o mesmo DocumentoFiscal
```

Não criar dois documentos para o mesmo intento por repetição de clique/retry.

---

## 6. Intenção de emissão

A chave de idempotência deve representar intenção estável.

Ela não deve depender de:

- timestamp atual;
- UUID aleatório;
- tentativa;
- número ainda não reservado.

Candidatos:

```text
venda_fiscal_id
modelo
ambiente
serie
```

Se futuramente existir reemissão/substituição legítima, deverá existir um identificador explícito de nova intenção.

---

## 7. Escolha do modelo

Modelos:

```text
55 = NF-e
65 = NFC-e
```

A escolha deve ser explícita no serviço.

Não inferir silenciosamente com base apenas no valor da venda.

Regras comerciais/fiscais futuras podem sugerir modelo, mas a camada deve receber uma decisão validada.

---

## 8. Ambiente

Valores:

```text
HOMOLOGACAO
PRODUCAO
```

O ambiente deve ser congelado ao criar o `DocumentoFiscal`.

Mudança posterior da configuração fiscal da matriz não deve modificar documento existente.

---

## 9. Série

A série deve ser fornecida por configuração fiscal do estabelecimento ou serviço responsável.

Não hardcode de forma espalhada.

O contrato da preparação deve receber a série já resolvida ou resolvê-la através de uma camada única.

---

## 10. Momento da reserva de número

Decisão arquitetural:

> não reservar número na criação inicial do RASCUNHO.

O `DocumentoFiscal` pode existir em RASCUNHO com:

```text
numero = NULL
```

A numeração deve ser consumida apenas quando o documento tiver passado por todas as validações necessárias para entrar em `PREPARADO`.

Fluxo:

```text
RASCUNHO
  -> validar payload
  -> validar obrigatorios
  -> reservar numero
  -> persistir numero
  -> PREPARADO
```

Isso reduz buracos desnecessários de numeração.

---

## 11. Atomicidade da reserva

A reserva do número já possui fundação em:

```text
SequenciaDocumentoFiscal
```

O processo de preparação deverá usar:

```text
transaction.atomic
+
select_for_update
```

O número reservado precisa ser persistido no `DocumentoFiscal` na mesma transação local.

Contrato:

```text
atomic:
    lock DocumentoFiscal
    validar estado
    reservar numero
    atribuir numero
    validar documento
    status -> PREPARADO
```

---

## 12. Concorrência

Duas requisições simultâneas para preparar a mesma intenção não podem:

- criar dois documentos;
- reservar dois números;
- transicionar duas vezes;
- produzir duplicidade de chave futura.

Será necessário lock no `DocumentoFiscal` ou criação idempotente protegida por constraint.

---

## 13. Estado inicial

Todo DocumentoFiscal nasce:

```text
RASCUNHO
```

Enquanto RASCUNHO:

- pode ainda não ter número;
- pode receber composição do payload interno;
- não pode ser transmitido;
- pode ser revalidado.

---

## 14. Critérios mínimos para PREPARADO

Antes de transicionar para `PREPARADO`, validar no mínimo:

### Documento

```text
venda_fiscal
matriz
loja
modelo
ambiente
serie
numero
idempotency_key
```

### Snapshot

```text
VendaFiscal existente
itens fiscais existentes
contexto fiscal existente
totais coerentes
```

### Itens

Cada `ItemVendaFiscal` deve possuir os campos fiscais obrigatórios aplicáveis ao layout futuro.

A implementação seguinte deverá mapear explicitamente quais campos são obrigatórios por modelo.

---

## 15. Integridade Matriz / Loja / Snapshot

O Documento Fiscal deve respeitar:

```text
DocumentoFiscal.matriz == VendaFiscal.venda.matriz
DocumentoFiscal.loja   == VendaFiscal.venda.loja
```

ou equivalente conforme contrato real do snapshot.

Não aceitar DocumentoFiscal apontando para snapshot de outro estabelecimento.

---

## 16. Payload interno

Antes de XML oficial, criar um DTO/payload interno estável.

Exemplo conceitual:

```python
@dataclass(frozen=True)
class DadosDocumentoFiscal:
    modelo: str
    ambiente: str
    serie: int
    numero: int | None
    emitente: ...
    destinatario: ...
    itens: tuple[...]
    totais: ...
```

Objetivo:

- separar Django model do layout XML;
- facilitar testes;
- facilitar troca de provider;
- permitir validação sem rede;
- evitar acessar banco durante montagem XML futura.

---

## 17. Payload de item

Exemplo conceitual:

```python
@dataclass(frozen=True)
class DadosItemDocumentoFiscal:
    sequencia: int
    produto_descricao: str
    ncm: str
    cest: str
    cfop: str
    cst_csosn: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal
    icms: ...
    pis: ...
    cofins: ...
    ipi: ...
```

A fonte é `ItemVendaFiscal`.

Nunca recalcular tributos nesta etapa.

---

## 18. Totais

Os totais do Documento Fiscal devem ser derivados do snapshot.

Não recalcular alíquotas.

Não consultar regra fiscal atual.

A preparação apenas consolida o que já foi congelado.

---

## 19. Destinatário

A camada de preparação deverá definir um contrato claro para dados do destinatário.

O snapshot atual precisa ser inspecionado para confirmar se todos os dados necessários já estão congelados.

Se faltarem dados documentais:

- CPF/CNPJ;
- nome;
- endereço;
- município;
- CEP;
- indicador IE;
- e-mail;

a lacuna deve ser registrada antes do XML oficial.

Não preencher silenciosamente com cadastro atual sem política explícita.

---

## 20. Emitente

Dados do emitente devem vir da configuração fiscal congelável do estabelecimento.

O Documento Fiscal deve registrar os dados históricos necessários para não depender de configuração futura mutável.

O Projeto seguinte deverá identificar exatamente quais dados ainda não estão congelados.

---

## 21. Chave de acesso

Nesta etapa, a chave ainda pode permanecer vazia.

A chave depende de:

- modelo;
- UF;
- CNPJ;
- série;
- número;
- tipo de emissão;
- código numérico;
- DV.

Portanto:

```text
RASCUNHO sem numero
-> sem chave
```

Após número reservado:

```text
PREPARADO
-> pode estar apto à futura geração da chave
```

A geração oficial da chave fica em etapa posterior.

---

## 22. XML

Fora do Projeto 191 e da primeira implementação de preparação:

```text
XML oficial
assinatura
schema XSD
namespace NF-e
canonicalizacao
certificado
```

O payload interno deve ser suficiente para preparar essa próxima camada.

---

## 23. Relação com finalizar_venda()

Não alterar `finalizar_venda()`.

Fluxo continua:

```text
finalizar_venda
-> snapshot fiscal
-> estoque
-> caixa
-> finaliza venda
```

Preparação documental será chamada por fluxo próprio posterior.

---

## 24. Quando criar DocumentoFiscal

Primeira decisão recomendada:

> criar DocumentoFiscal apenas quando existir intenção explícita de emissão.

Não criar automaticamente para toda venda não fiscal.

Para venda fiscal:

- pode haver criação logo após fechamento por orquestração futura;
- mas isso deve ocorrer fora da transação comercial principal.

---

## 25. Falha de preparação

Se a preparação falhar antes da reserva de número:

```text
RASCUNHO
+
erro registrado
```

ou rollback integral, conforme service.

Se falhar depois da reserva do número dentro da mesma transação:

```text
rollback
```

e o incremento da sequência também deve ser revertido.

---

## 26. Repetição após falha

Retry deve:

- localizar o mesmo DocumentoFiscal por idempotency_key;
- não criar outro;
- revalidar estado;
- reservar número apenas se ainda não houver número;
- não consumir múltiplos números por retry.

---

## 27. Regras de estado para preparação

Permitido:

```text
RASCUNHO -> PREPARADO
```

Não permitido pelo service de preparação:

```text
AUTORIZADO -> PREPARADO
CANCELADO -> PREPARADO
DENEGADO -> PREPARADO
TRANSMITINDO -> PREPARADO
```

`REJEITADO -> PREPARADO` pertence ao fluxo de correção/reenvio já previsto na máquina de estados, não ao primeiro preparo da intenção original.

---

## 28. Auditoria

Preparação deverá futuramente registrar:

- documento criado;
- documento reutilizado por idempotência;
- número reservado;
- transição para PREPARADO;
- falha de validação.

Não incluir secrets.

---

## 29. Testes mínimos da implementação seguinte

A futura implementação deverá testar:

1. cria DocumentoFiscal em RASCUNHO;
2. chamada repetida retorna o mesmo documento;
3. intenção diferente cria documento distinto quando permitido;
4. não reserva número no RASCUNHO;
5. reserva número ao preparar;
6. reserva dentro de transação;
7. retry não consome outro número;
8. duas sequências independentes por loja/modelo/ambiente/série;
9. snapshot inválido bloqueia preparação;
10. documento preparado possui número;
11. transição incorreta é bloqueada;
12. nenhuma chamada de rede;
13. `finalizar_venda()` permanece intacto.

---

## 30. Escopo sugerido da Implementação 192

Criar apenas:

```text
fiscal/dto_documento_fiscal.py
fiscal/services_preparacao_documento_fiscal.py
testes
```

Possível ajuste mínimo de model somente se o contrato identificar lacuna inevitável.

Preferência:

> não criar nova migration na 192, se a fundação atual já for suficiente.

---

## 31. Fora da Implementação 192

Continuam fora:

```text
SEFAZ
provider
requests/httpx
XML oficial
assinatura
certificado
CSC
QR Code
DANFE
cancelamento externo
contingencia real
```

---

## 32. Gate arquitetural

Antes da Implementação 192 confirmar:

- [ ] snapshot é a única fonte tributária;
- [ ] não recalcular tributos;
- [ ] criação é idempotente;
- [ ] RASCUNHO nasce sem número;
- [ ] número só é reservado na preparação;
- [ ] reserva e PREPARADO ficam na mesma transação;
- [ ] retry não consome outro número;
- [ ] payload interno é independente do XML;
- [ ] emitente/destinatário possuem política histórica definida;
- [ ] chave de acesso ainda não é gerada oficialmente;
- [ ] finalizar_venda() não muda;
- [ ] não há rede externa.

---

## 33. Decisão final

Arquitetura aprovada:

```text
VendaFiscal + ItemVendaFiscal
        |
        v
criar/recuperar DocumentoFiscal por idempotencia
        |
        v
RASCUNHO sem numero
        |
        v
construir payload interno
        |
        v
validar completude
        |
        v
transaction.atomic
        |
        +--> lock documento
        +--> reservar numero
        +--> persistir numero
        +--> RASCUNHO -> PREPARADO
        |
        v
DocumentoFiscal PREPARADO
```

Somente depois disso uma etapa futura poderá montar chave, XML, assinatura e transmissão.