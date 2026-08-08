# PDV-05B.5 — Projeto 162

## Título

Painel Fiscal Efetivo do Produto

## Objetivo

Integrar a infraestrutura tributária já consolidada ao detalhe/cadastro do Produto, exibindo a classificação fiscal efetiva calculada a partir do contexto operacional oficial.

A interface deverá consumir os serviços existentes sem duplicar regras tributárias, sem calcular impostos monetários e sem persistir resultados de simulação.

## Branch obrigatória

```text
feature/pdv-05b-4-motor-tributario-produto
```

Enquanto esta feature não for encerrada e mergeada, toda evolução da PDV-05B.5 permanecerá nesta branch.

Nenhuma alteração deverá ser aplicada diretamente em `master` ou `develop`.

## Infraestrutura já disponível

A sprint parte das seguintes camadas homologadas:

```text
ConfiguracaoFiscalMatriz
        ↓
construir_contexto_tributario(...)
        ↓
ContextoSelecaoFiscal
        ↓
Motor de Seleção
        ↓
resolver_produto_fiscal(...)
        ↓
ProdutoFiscalResolvido
```

O Painel Fiscal será apenas consumidor dessa cadeia.

## Princípio principal

A view não deverá:

- decidir CST;
- decidir CSOSN;
- selecionar Regra Fiscal;
- resolver benefício fiscal;
- normalizar UF manualmente;
- interpretar regime tributário;
- montar regra tributária paralela;
- calcular imposto.

Toda decisão deverá vir de services do domínio fiscal.

## Escopo da Sprint

### Etapa 1 — Contexto do Produto

A view deverá obter:

- Matriz do contexto operacional;
- Loja, quando disponível;
- Produto;
- UF de destino para consulta.

Como o detalhe do Produto não representa uma venda concreta, a UF de destino não deverá ser inventada.

A interface deverá trabalhar em dois estados:

```text
Sem UF de destino
    → painel informativo / contexto incompleto

Com UF de destino
    → resolução fiscal efetiva
```

## Etapa 2 — Serviço de apresentação

Criar uma camada específica para a interface, por exemplo:

```text
produtos/services/fiscal/painel_produto_fiscal.py
```

Contrato proposto:

```python
def montar_painel_fiscal_produto(
    *,
    produto,
    matriz,
    loja=None,
    uf_destino=None,
    data_operacao=None,
):
    ...
```

Esse serviço deverá:

1. validar disponibilidade de configuração fiscal;
2. construir contexto tributário quando houver dados suficientes;
3. chamar `resolver_produto_fiscal`;
4. converter o resultado em um objeto de apresentação;
5. nunca persistir dados.

## DTO de apresentação

Criar um objeto imutável específico para UI:

```python
@dataclass(frozen=True, slots=True)
class PainelFiscalProduto:
    status: str

    regime_tributario: str = ""
    uf_origem: str = ""
    uf_destino: str = ""

    regra_codigo: str = ""
    regra_nome: str = ""
    origem_regra: str = ""

    origem_mercadoria: str = ""

    ncm: str = ""
    cest: str = ""

    cst_icms: str = ""
    csosn: str = ""
    cst_pis: str = ""
    cst_cofins: str = ""
    cst_ipi: str = ""

    beneficio: str = ""

    observacoes: tuple[str, ...] = ()
    alertas: tuple[str, ...] = ()
```

Esse DTO não deverá conter models mutáveis quando não forem necessários para renderização.

## Status do painel

Status candidatos:

```text
valido
configuracao_fiscal_ausente
contexto_incompleto
sem_regra
ambigua
contexto_invalido
```

A validação deverá preferencialmente reutilizar status já existentes em `ProdutoFiscalResolvido` quando possível.

## Regra de origem da resolução

O painel deverá informar de forma explícita:

```text
Regra vinculada ao Produto
```

ou:

```text
Regra selecionada pelo Motor
```

Não deverá tentar deduzir isso no template.

Essa informação deverá vir pronta do service de apresentação.

## Fluxo da resolução

```text
View Produto
    │
    ▼
montar_painel_fiscal_produto
    │
    ├── sem UF destino
    │       ↓
    │   contexto incompleto
    │
    └── com UF destino
            ↓
    construir_contexto_tributario
            ↓
    resolver_produto_fiscal
            ↓
    PainelFiscalProduto
```

## Tela do Produto

O bloco deverá aparecer no detalhe fiscal do Produto com o título:

```text
CLASSIFICAÇÃO FISCAL EFETIVA
```

Exemplo:

```text
CLASSIFICAÇÃO FISCAL EFETIVA

Regime ............. Regime Normal
Origem ............. SP
Destino ............ RJ

Regra .............. VENDA-INTERESTADUAL
Origem da regra .... Motor Tributário

NCM ................ 21069090
CEST ............... 17.123.00

ICMS ............... CST 00
PIS ................ 01
COFINS ............. 01
IPI ................ 50

Benefício .......... Nenhum

Status ............. Configuração válida
```

## Estado sem UF de destino

Quando o Produto for acessado sem uma operação concreta:

```text
Status: Contexto incompleto

Informe a UF de destino para visualizar a classificação fiscal efetiva.
```

O painel poderá ainda exibir informações independentes da UF, como:

- regime tributário da Matriz;
- UF de origem;
- NCM;
- CEST;
- origem da mercadoria.

Mas não deverá afirmar qual Regra Fiscal será utilizada.

## Entrada de UF de destino

Nesta primeira versão, a UF de destino deverá ser informada somente para consulta.

Opção proposta:

```text
<select name="uf_destino">
```

A consulta poderá utilizar GET:

```text
/produtos/<id>/?uf_destino=RJ
```

Vantagens:

- não persiste estado;
- URL reproduzível;
- simples de testar;
- sem AJAX obrigatório;
- não exige migration.

## Botão

O painel deverá possuir:

```text
Atualizar Classificação
```

ou:

```text
Consultar Tributação
```

A Simulação Tributária completa continuará fora desta sprint.

## View

A view de detalhe deverá:

1. obter o contexto operacional;
2. obter o Produto da Matriz;
3. ler `uf_destino` da query string;
4. chamar `montar_painel_fiscal_produto`;
5. enviar o resultado ao template.

A view não deverá construir `ContextoSelecaoFiscal` diretamente.

## Template

O template deverá apenas apresentar dados.

Não permitido:

```django
{% if produto.regra_fiscal_padrao %}
    ...
{% endif %}
```

para decidir regra efetiva.

Não permitido:

```django
{% if regime == "simples" %}
```

para decidir CST/CSOSN.

Toda decisão fiscal deverá chegar pronta.

## Tratamento de erros

Erros de contexto previsíveis deverão virar estados do painel, e não erro HTTP 500.

Exemplos:

### Sem configuração fiscal

```text
A Matriz ainda não possui configuração fiscal ativa.
```

### Sem UF destino

```text
Informe a UF de destino para concluir a resolução fiscal.
```

### Sem regra

```text
Nenhuma Regra Fiscal aplicável foi encontrada para este contexto.
```

### Ambiguidade

```text
Mais de uma Regra Fiscal possui a mesma prioridade para este contexto.
```

### Contexto inválido

```text
O contexto tributário informado é inválido.
```

## Permissões

O painel poderá ser visível para usuários que já possuem acesso ao detalhe do Produto.

A alteração de configuração fiscal continuará protegida por:

```python
PERMISSAO_FISCAL_CONFIGURAR
```

Consultar a classificação não deverá conceder permissão para editar cadastros fiscais.

## Auditoria

A consulta do painel não precisará registrar auditoria nesta etapa, pois é operação somente leitura.

Alterações futuras de configuração permanecem auditadas pelos services correspondentes.

## Migration

Expectativa:

```text
nenhuma migration
```

A aplicação deverá ser bloqueada se `makemigrations --check --dry-run` detectar alteração.

## Arquivos previstos

```text
produtos/services/fiscal/painel_produto_fiscal.py
produtos/tests/services/fiscal/test_painel_produto_fiscal.py
produtos/views.py
produtos/templates/produtos/detalhe_produto.html
docs/arquitetura/pdv-05b-5-painel-fiscal-produto.md
docs/usabilidade/fiscal/painel-fiscal-produto.md
```

Os caminhos reais de view e template deverão ser confirmados pelo diagnóstico antes da aplicação.

## Testes do service

1. retorna contexto incompleto sem UF destino;
2. retorna configuração ausente sem erro técnico;
3. resolve regra vinculada diretamente ao Produto;
4. resolve regra pelo Motor;
5. expõe origem da regra;
6. apresenta CST para regime normal;
7. apresenta CSOSN para Simples Nacional;
8. apresenta NCM e CEST;
9. apresenta benefício;
10. propaga status sem regra;
11. propaga ambiguidade;
12. propaga contexto inválido;
13. não persiste Produto;
14. não altera configuração fiscal.

## Testes da view

1. detalhe sem UF destino renderiza;
2. detalhe com UF destino válida renderiza resultado;
3. UF inválida não gera erro 500;
4. Produto de outra Matriz continua bloqueado;
5. usuário sem contexto válido continua respeitando regras atuais;
6. query string não persiste valor;
7. template não executa lógica tributária.

## Regressão obrigatória

Executar:

```text
fiscal.tests.test_contexto_tributario
fiscal.tests.test_configuracao_fiscal_matriz
fiscal.tests.test_motor_selecao_regra_fiscal
fiscal.tests.test_regra_fiscal
produtos.tests.services.fiscal.test_resolver_produto_fiscal
produtos.tests.test_produto_fiscal_model
```

Além dos testes atuais da view/detalhe do Produto identificados pelo diagnóstico.

## Homologação visual

Após testes automatizados:

1. abrir Produto sem UF destino;
2. confirmar estado de contexto incompleto;
3. consultar SP;
4. consultar outra UF;
5. confirmar Regra Fiscal exibida;
6. confirmar CST ou CSOSN;
7. confirmar NCM e CEST;
8. confirmar layout responsivo;
9. confirmar ausência de duplicidade com o bloco fiscal cadastral já existente.

## Diagnóstico 163

Antes da aplicação, mapear:

1. view real de detalhe do Produto;
2. template real;
3. rota real;
4. contexto operacional utilizado;
5. componentes CSS existentes;
6. testes atuais da tela;
7. forma como o bloco fiscal cadastral está organizado;
8. assinatura atual de `ProdutoFiscalResolvido`;
9. diferença entre regra direta e regra selecionada pelo Motor;
10. status disponíveis no resolver;
11. comportamento com UF destino inválida;
12. ausência de migrations pendentes.

## Critérios de sucesso

A sprint será aprovada quando:

- painel consumir somente services;
- template não possuir regra tributária;
- UF destino não for inventada;
- sem UF destino não gerar erro;
- regra efetiva estiver claramente identificada;
- CST/CSOSN respeitarem o regime;
- nenhum model for alterado;
- nenhuma migration for criada;
- testes novos e regressão passarem;
- homologação visual for aprovada;
- nenhum commit automático for realizado.

## Critérios de rollback

Rollback automático se:

- branch estiver incorreta;
- service duplicar Motor de Seleção;
- view montar contexto fiscal manualmente;
- template decidir regra fiscal;
- migration for criada;
- testes falharem;
- regressão falhar;
- painel alterar Produto;
- consulta persistir UF destino;
- comportamento atual do cadastro fiscal do Produto quebrar.

## Resultado esperado

Ao final da PDV-05B.5, o usuário conseguirá abrir um Produto, informar uma UF de destino e visualizar a classificação fiscal efetiva que o ERP utilizaria naquele contexto, com rastreabilidade sobre a Regra Fiscal aplicada e sem cálculo monetário de tributos.
