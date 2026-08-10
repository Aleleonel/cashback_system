# PDV-05C.2 — Projeto 187 — Contrato do Documento Fiscal e Máquina de Estados

## 1. Objetivo

Definir a camada interna de Documento Fiscal eletrônico sem ainda transmitir para SEFAZ, assinar XML, gerar DANFE/QR Code ou integrar provider externo.

A base já existente permanece responsável pelo fato tributário histórico:

- VendaFiscal;
- ItemVendaFiscal;
- resolução fiscal;
- cálculo tributário;
- snapshot imutável;
- integração fiscal no fechamento da venda.

O Documento Fiscal será uma nova camada, nunca uma substituição do snapshot.

## 2. Fronteira arquitetural

```text
Venda
  -> VendaFiscal / ItemVendaFiscal
  -> DocumentoFiscal
  -> montagem XML/payload
  -> assinatura
  -> GatewayFiscal
  -> SEFAZ / provider
  -> eventos
  -> DANFE / QR Code
```

Responsabilidades:

- Venda: fato comercial.
- VendaFiscal: fato tributário congelado.
- DocumentoFiscal: identidade e ciclo eletrônico.
- GatewayFiscal: comunicação externa.

## 3. Localização do agregado

Decisão: `DocumentoFiscal` deve viver no app `fiscal`.

Motivos:

- não é responsabilidade exclusiva do PDV;
- poderá ser reutilizado por devoluções, compras, transferências e eventos;
- evita acoplamento do `pdv` com SEFAZ/provider;
- preserva separação entre operação comercial e domínio fiscal.

## 4. Modelos fiscais

Modelos iniciais:

```text
55 = NF-e
65 = NFC-e
```

Devem usar enum/choices explícitos.

## 5. Relação com VendaFiscal

Relação proposta:

```text
VendaFiscal 1 ---- N DocumentoFiscal
```

Não adicionar número, série, XML, protocolo ou chave diretamente em `VendaFiscal`.

## 6. Campos conceituais mínimos

Identidade:

```text
id
uuid
venda_fiscal
matriz
loja
```

Caracterização:

```text
modelo
ambiente
serie
numero
```

Chave:

```text
chave_acesso
codigo_numerico
digito_verificador
```

Estado:

```text
status
tentativa_atual
```

Conteúdo:

```text
xml_rascunho
xml_assinado
xml_autorizado
```

Autorização:

```text
codigo_status
motivo_status
protocolo_autorizacao
data_autorizacao
```

Controle:

```text
idempotency_key
criado_em
atualizado_em
ultima_tentativa_em
```

A implementação 188 deverá decidir quais campos XML ficam no model principal e quais podem ser separados.

## 7. Máquina de estados

Estados mínimos:

```text
RASCUNHO
PREPARADO
PENDENTE_TRANSMISSAO
TRANSMITINDO
AUTORIZADO
REJEITADO
DENEGADO
CONTINGENCIA
CANCELADO
ERRO
```

Semântica:

- RASCUNHO: documento interno ainda editável.
- PREPARADO: validado localmente.
- PENDENTE_TRANSMISSAO: pronto para fila/outbox.
- TRANSMITINDO: tentativa externa em andamento.
- AUTORIZADO: autorizado pelo fisco, conteúdo imutável.
- REJEITADO: rejeição formal corrigível conforme regra.
- DENEGADO: resultado fiscal próprio, diferente de erro técnico.
- CONTINGENCIA: fluxo especial futuro.
- CANCELADO: cancelamento homologado.
- ERRO: falha técnica local/transporte.

## 8. Transições permitidas

```text
RASCUNHO
  -> PREPARADO
  -> ERRO

PREPARADO
  -> PENDENTE_TRANSMISSAO
  -> RASCUNHO
  -> ERRO

PENDENTE_TRANSMISSAO
  -> TRANSMITINDO
  -> ERRO

TRANSMITINDO
  -> AUTORIZADO
  -> REJEITADO
  -> DENEGADO
  -> CONTINGENCIA
  -> ERRO

REJEITADO
  -> PREPARADO
  -> ERRO

CONTINGENCIA
  -> TRANSMITINDO
  -> AUTORIZADO
  -> ERRO

AUTORIZADO
  -> CANCELADO
```

Transições não previstas devem ser rejeitadas por service de domínio.

## 9. Estados terminais

Conteúdo fiscal não deve ser alterado após:

```text
AUTORIZADO
DENEGADO
CANCELADO
```

`AUTORIZADO` pode receber eventos, mas seu conteúdo original não deve ser reescrito.

## 10. Idempotência

A mesma intenção de emissão não pode criar dois documentos autorizados por repetição acidental.

A implementação deverá definir uma `idempotency_key` baseada em identidade estável.

Candidato conceitual:

```text
matriz + loja + venda_fiscal + modelo + ambiente
```

A constraint física será definida no Projeto 188.

## 11. Número e série

Numeração fiscal deve possuir controle concorrente.

Nunca usar simplesmente:

```text
ultimo_numero + 1
```

sem lock.

Estrutura futura sugerida:

```text
SequenciaDocumentoFiscal
- estabelecimento
- modelo
- ambiente
- serie
- proximo_numero
```

Requisitos:

- escopo por estabelecimento;
- modelo;
- ambiente;
- série;
- `select_for_update()` ou mecanismo equivalente;
- unicidade;
- rastreabilidade.

## 12. Chave de acesso

A chave pertence ao DocumentoFiscal, não ao snapshot.

Requisitos:

- validação de formato/tamanho;
- unicidade quando preenchida;
- imutabilidade após autorização;
- não gerar chave fictícia para documento ainda não numerado.

## 13. XML

Fluxo futuro obrigatório:

```text
snapshot
-> DTO do documento
-> validação
-> XML
-> assinatura
-> transmissão
```

Nunca:

```text
Venda -> XML diretamente
```

Separar conceitualmente:

```text
payload interno
XML gerado
XML assinado
XML autorizado
```

## 14. Certificado digital

Certificado e senha não devem ser armazenados diretamente em DocumentoFiscal.

A futura configuração deverá usar referência segura/secret storage.

Nunca registrar em log:

- senha;
- PFX/P12 bruto;
- chave privada;
- token secreto.

## 15. CSC NFC-e

CSC é configuração de estabelecimento/ambiente, não dado do documento.

Documento histórico pode armazenar identificador necessário à auditoria, evitando persistir o segredo puro.

## 16. Ambiente

Valores mínimos:

```text
HOMOLOGACAO
PRODUCAO
```

O ambiente deve ser congelado no documento no momento da criação.

Mudança posterior da configuração não pode modificar documento histórico.

## 17. Estratégia de transmissão

A arquitetura deve nascer preparada para fila/outbox.

Fluxo:

```text
PREPARADO
-> PENDENTE_TRANSMISSAO
-> worker/outbox
-> TRANSMITINDO
-> resultado
```

Nenhum worker será criado no 187.

## 18. Relação com finalizar_venda()

`finalizar_venda()` não deve transmitir à SEFAZ.

Fluxo comercial permanece:

```text
finalizar_venda
-> snapshot fiscal
-> estoque
-> caixa
-> venda finalizada
```

A emissão ocorre posteriormente por service específico.

Motivo: não manter estoque/caixa dependentes de rede externa.

## 19. Fronteira transacional

Operações locais podem usar transações curtas.

Regra arquitetural:

```text
transaction.atomic()
    persistir intenção
COMMIT

chamada externa

transaction.atomic()
    persistir resultado
COMMIT
```

Nunca manter transação longa aberta durante chamada de rede.

## 20. Eventos fiscais

Eventos futuros devem possuir agregado próprio:

```text
EventoDocumentoFiscal
```

Tipos previstos:

```text
CANCELAMENTO
INUTILIZACAO
CONTINGENCIA
```

Eventos não sobrescrevem documento autorizado.

## 21. Cancelamento

Cancelamento é evento posterior à autorização.

Não apagar:

- DocumentoFiscal;
- VendaFiscal;
- XML autorizado.

Estado final só vira `CANCELADO` após confirmação externa.

## 22. Inutilização

Inutilização refere-se a faixa de numeração e não necessariamente a uma venda.

Não deve ser simples status de `Venda`.

## 23. Contingência

Reservar contrato para:

- estado;
- tipo de emissão;
- timestamp;
- justificativa;
- sincronização posterior.

Regras estaduais específicas ficam fora desta etapa.

## 24. DANFE e QR Code

DANFE é representação do documento autorizado.

```text
DocumentoFiscal autorizado
-> representação
-> HTML/PDF/80mm/QR Code
```

O atual `pdv/templates/pdv/cupom_venda_80mm.html` continua sendo cupom comercial/não fiscal.

Não chamá-lo de DANFE NFC-e.

## 25. Gateway fiscal

Domínio não deve importar SDK específico de provider.

Contrato futuro:

```python
class GatewayFiscal(Protocol):
    def transmitir(...)
    def consultar(...)
    def cancelar(...)
```

Adapters possíveis:

```text
SefazDiretoGateway
ProviderFiscalGateway
```

## 26. Erros

Separar:

```text
ErroTecnicoFiscal
RejeicaoFiscal
DenegacaoFiscal
```

Erro técnico pode ser retry.

Rejeição possui código e motivo formal.

Denegação possui semântica própria.

## 27. Auditoria

Registrar em transições:

- estado anterior;
- estado novo;
- usuário/processo;
- timestamp;
- tentativa;
- código/motivo;
- correlação/idempotência.

## 28. Segurança

Não logar:

- senha de certificado;
- certificado bruto;
- CSC;
- token de API;
- secrets.

XML autorizado deve possuir controle de acesso.

## 29. Imutabilidade

Após `AUTORIZADO`, não alterar:

- modelo;
- série;
- número;
- chave;
- XML autorizado;
- protocolo;
- snapshot de origem.

Correções devem ocorrer por eventos/documentos apropriados.

## 30. Escopo recomendado do Projeto 188

Implementar apenas fundação interna:

1. `DocumentoFiscal`;
2. choices de modelo;
3. choices de ambiente;
4. choices de status;
5. máquina de estados em service;
6. vínculo com `VendaFiscal`;
7. constraints básicas;
8. testes de transição;
9. admin mínimo;
10. migration.

Fora do 188:

- SEFAZ;
- provider;
- certificado;
- CSC;
- XML oficial;
- QR Code;
- DANFE;
- cancelamento real;
- contingência real.

## 31. Gate arquitetural

Antes da implementação 188, confirmar:

- DocumentoFiscal fica no app fiscal.
- VendaFiscal continua imutável.
- DocumentoFiscal referencia VendaFiscal.
- modelo 55/65 usa enum.
- ambiente é congelado.
- numeração possui controle concorrente.
- máquina de estados fica em service.
- transmissão não ocorre em `finalizar_venda()`.
- chamada externa não mantém transação longa.
- idempotência está prevista.
- eventos não sobrescrevem documento autorizado.
- cupom comercial atual não é DANFE.
- provider é adapter.
- secrets ficam fora de models comuns.

## 32. Decisão final

```text
PDV
  -> Venda
  -> VendaFiscal + ItemVendaFiscal
  -> DocumentoFiscal
  -> Gerador XML/payload
  -> Assinatura
  -> GatewayFiscal
  -> SEFAZ/provider
  -> Eventos
  -> DANFE/QR Code
```

Essa separação preserva o fechamento já homologado e permite evoluir emissão fiscal sem transformar o PDV em cliente direto da SEFAZ.