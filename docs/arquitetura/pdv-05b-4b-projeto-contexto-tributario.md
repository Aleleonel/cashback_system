# PDV-05B.4B — Projeto 159

## Título

Construtor do Contexto Tributário

## Objetivo

Criar uma camada única e reutilizável para montar o contexto tributário operacional consumido pelo Motor de Seleção, pelo Resolver Fiscal do Produto e pelas futuras rotinas de PDV, Compras, NF-e e NFC-e.

O componente não deverá selecionar regra fiscal, calcular impostos ou persistir dados.

## Branch obrigatória

```text
feature/pdv-05b-4-motor-tributario-produto
```

Nenhuma alteração poderá ser aplicada diretamente em `master` ou `develop`.

## Princípio arquitetural

Nenhum módulo deverá montar manualmente os dados exigidos pelo Motor de Seleção.

A direção correta da dependência será:

```text
ConfiguracaoFiscalMatriz
        ↓
Construtor do Contexto Tributário
        ↓
ContextoSelecaoFiscal
        ↓
Motor de Seleção
        ↓
Regra Fiscal
        ↓
Resolver do Produto
```

## Decisão sobre DTO

O projeto deverá reutilizar `ContextoSelecaoFiscal` como contrato final entregue ao Motor de Seleção.

Não será criado um segundo DTO com os mesmos campos.

Caso seja necessário transportar metadados adicionais do processo de construção, será criado um resultado imutável separado:

```python
ContextoTributarioConstruido
```

Esse resultado poderá conter:

```text
contexto
configuracao_fiscal
alertas
observacoes
status
```

## Estrutura proposta

```text
fiscal/
    services_contexto_tributario.py
    selectors_configuracao_fiscal.py
    domain/
        selecao_fiscal.py
    tests/
        test_contexto_tributario.py
```

## Value object proposto

```python
@dataclass(frozen=True)
class ContextoTributarioConstruido:
    contexto: ContextoSelecaoFiscal | None
    configuracao_fiscal: ConfiguracaoFiscalMatriz | None
    status: StatusContextoTributario
    alertas: tuple[str, ...] = ()
    observacoes: tuple[str, ...] = ()
```

## Status propostos

```python
class StatusContextoTributario(StrEnum):
    VALIDO = "valido"
    CONFIGURACAO_AUSENTE = "configuracao_ausente"
    CONFIGURACAO_INATIVA = "configuracao_inativa"
    CONTEXTO_INCOMPLETO = "contexto_incompleto"
    CONTEXTO_INVALIDO = "contexto_invalido"
```

A validação 160 deverá confirmar compatibilidade com a versão de Python usada pelo projeto antes de adotar `StrEnum`.

Caso necessário, utilizar:

```python
class StatusContextoTributario(str, Enum):
    ...
```

## Service principal

Arquivo:

```text
fiscal/services_contexto_tributario.py
```

Contrato proposto:

```python
def construir_contexto_tributario(
    *,
    matriz,
    loja=None,
    produto=None,
    cliente=None,
    data_operacao=None,
    tipo_operacao="saida",
    finalidade_operacao="venda",
    uf_destino=None,
    contribuinte_icms=None,
    consumidor_final=None,
) -> ContextoTributarioConstruido:
    ...
```

## Fontes oficiais dos dados

### Regime tributário

Origem:

```python
ConfiguracaoFiscalMatriz.regime_tributario
```

### UF de origem

Origem:

```python
ConfiguracaoFiscalMatriz.uf_origem
```

### Contribuinte do ICMS

Prioridade:

1. valor explicitamente informado pela operação;
2. valor obtido do cliente, quando houver contrato confiável;
3. `ConfiguracaoFiscalMatriz.contribuinte_icms`.

### Consumidor final

Prioridade:

1. valor explicitamente informado pela operação;
2. valor obtido do cliente, quando houver contrato confiável;
3. `ConfiguracaoFiscalMatriz.consumidor_final_padrao`.

### UF de destino

Prioridade:

1. valor explicitamente informado;
2. endereço fiscal do cliente, quando houver contrato confiável;
3. ausente.

A UF da própria Matriz ou Loja não poderá ser usada automaticamente como destino.

### NCM e CEST

Origem:

```python
produto.ncm
produto.cest
```

Somente quando o Produto for informado.

### Matriz e Loja

- Matriz obrigatória.
- Loja opcional.
- Loja informada deverá pertencer à Matriz.

## Data da operação

Quando não informada:

```python
date.today()
```

Esse default é operacional, não fiscal, e não altera dados persistidos.

## Regras de validação

### Matriz

- obrigatória;
- deve existir;
- não poderá ser inferida de Produto ou Cliente.

### Loja

- opcional;
- quando informada, deve pertencer à Matriz.

### Configuração fiscal

- deve existir;
- deve estar ativa;
- deve estar pronta para operação;
- não poderá ser criada automaticamente pelo builder.

### Regime tributário

- deve vir exclusivamente da configuração fiscal ativa.

### UF de origem

- deve vir exclusivamente da configuração fiscal ativa;
- deve estar normalizada e válida.

### UF de destino

- pode ser ausente em telas sem operação concreta;
- ausência deverá gerar contexto incompleto ou alerta controlado;
- não deverá causar erro 500.

### Produto

- opcional;
- quando informado, NCM e CEST poderão enriquecer o contexto;
- o builder não deve alterar o Produto.

### Cliente

- opcional;
- o builder somente deverá ler dados cuja origem tenha contrato comprovado;
- campos não comprovados não deverão ser inferidos.

## Comportamento sem configuração fiscal

Quando a Matriz não possuir configuração fiscal ativa:

```python
ContextoTributarioConstruido(
    contexto=None,
    configuracao_fiscal=None,
    status=StatusContextoTributario.CONFIGURACAO_AUSENTE,
    alertas=("A matriz nao possui configuracao fiscal ativa.",),
)
```

Nenhuma exceção técnica deverá escapar para a interface.

## Comportamento com configuração inativa

O selector atual retorna apenas configuração ativa.

A validação 160 deverá decidir entre:

1. manter o selector atual e classificar como `CONFIGURACAO_AUSENTE`; ou
2. criar selector adicional que localize a configuração, independentemente do estado, permitindo diferenciar ausência de inatividade.

A recomendação arquitetural é a opção 2.

## Contratos de selectors propostos

```python
def get_configuracao_fiscal_matriz(*, matriz):
    ...
```

Retorna somente configuração ativa.

```python
def get_configuracao_fiscal_matriz_existente(*, matriz):
    ...
```

Retorna a configuração independentemente do estado.

Nenhum selector poderá criar ou atualizar registros.

## Construção de ContextoSelecaoFiscal

Exemplo conceitual:

```python
contexto = ContextoSelecaoFiscal(
    data_operacao=data_operacao,
    regime_tributario=configuracao.regime_tributario,
    tipo_operacao=tipo_operacao,
    finalidade_operacao=finalidade_operacao,
    uf_origem=configuracao.uf_origem,
    uf_destino=uf_destino,
    matriz=matriz,
    loja=loja,
    contribuinte_icms=contribuinte_icms_resolvido,
    consumidor_final=consumidor_final_resolvido,
    ncm=getattr(produto, "ncm", None),
    cest=getattr(produto, "cest", None),
)
```

A assinatura real deverá ser confirmada pela validação 160.

## O que entra nesta sprint

- resultado imutável da construção;
- enum de status;
- builder;
- selector adicional, se necessário;
- validação de Matriz e Loja;
- leitura da `ConfiguracaoFiscalMatriz`;
- integração com `ContextoSelecaoFiscal`;
- testes;
- documentação técnica;
- documentação de usabilidade.

## O que não entra nesta sprint

- seleção de Regra Fiscal;
- cálculo monetário de impostos;
- painel visual;
- simulação tributária;
- rota;
- view;
- template;
- AJAX;
- persistência de contexto;
- criação automática de configuração fiscal;
- edição de configuração fiscal;
- integração direta com NF-e ou NFC-e;
- alteração de models;
- nova migration, salvo necessidade comprovada.

## Migration

A expectativa é:

```text
nenhuma migration
```

O projeto deverá ser bloqueado caso `makemigrations --check --dry-run` detecte alterações inesperadas.

## Testes obrigatórios

### Configuração

1. retorna status de configuração ausente;
2. diferencia configuração inativa, se houver selector apropriado;
3. rejeita configuração incompleta;
4. utiliza configuração ativa válida.

### Matriz e Loja

1. exige Matriz;
2. aceita Loja da mesma Matriz;
3. rejeita Loja de outra Matriz;
4. funciona sem Loja.

### Operação

1. utiliza data informada;
2. utiliza `date.today()` quando ausente;
3. preserva tipo e finalidade;
4. não seleciona Regra Fiscal.

### UF

1. utiliza UF de origem da configuração;
2. utiliza UF de destino explícita;
3. aceita destino ausente de forma controlada;
4. rejeita UF inválida;
5. não usa UF da Loja como destino implicitamente.

### Produto

1. funciona sem Produto;
2. utiliza NCM do Produto;
3. utiliza CEST do Produto;
4. não altera Produto.

### Contribuinte e consumidor final

1. valor explícito prevalece;
2. configuração fornece fallback;
3. valores `False` são preservados;
4. `None` não é confundido com `False`.

### Imutabilidade

1. resultado não pode ser alterado;
2. alertas e observações são tuplas;
3. contexto entregue não é reconstruído por módulos consumidores.

### Regressão

Devem continuar passando:

```text
fiscal.tests.test_configuracao_fiscal_matriz
fiscal.tests.test_motor_selecao_regra_fiscal
fiscal.tests.test_regra_fiscal
produtos.tests.services.fiscal.test_resolver_produto_fiscal
produtos.tests.test_produto_fiscal_model
```

## Validação 160

Antes da aplicação, o diagnóstico deverá confirmar:

1. assinatura real de `ContextoSelecaoFiscal`;
2. enum ou estados já existentes no domínio fiscal;
3. tipos de `ncm` e `cest` no Produto;
4. relacionamento real entre Loja e Matriz;
5. campos fiscais disponíveis no Cliente;
6. comportamento atual de normalização de UF;
7. uso atual de `date.today()` no Motor de Seleção;
8. versão de Python e suporte a `StrEnum`;
9. organização real dos services fiscais;
10. ausência de builder equivalente;
11. ausência de migration pendente;
12. impacto do selector para configuração inativa.

## Arquivos previstos para a aplicação

```text
fiscal/services_contexto_tributario.py
fiscal/selectors_configuracao_fiscal.py
fiscal/tests/test_contexto_tributario.py
docs/arquitetura/pdv-05b-4b-contexto-tributario.md
docs/usabilidade/fiscal/contexto-tributario.md
```

Poderá ser criado um arquivo de domínio separado:

```text
fiscal/domain/contexto_tributario.py
```

caso o projeto já utilize esse padrão.

## Critérios de sucesso

A aplicação futura será aprovada quando:

- nenhum model for alterado;
- nenhuma migration for criada;
- builder utilizar somente fontes oficiais;
- ausência de configuração não gerar erro 500;
- Loja incompatível for rejeitada;
- contexto final for imutável;
- todos os testes novos passarem;
- regressões fiscais e de Produto passarem;
- `manage.py check` passar;
- `makemigrations --check --dry-run` retornar `No changes detected`;
- nenhum commit automático for criado.

## Critérios de rollback

Rollback automático se:

- branch estiver incorreta;
- builder equivalente já existir;
- assinatura real de `ContextoSelecaoFiscal` divergir;
- surgir ciclo de importação;
- alguma migration for gerada;
- qualquer teste falhar;
- o builder selecionar Regra Fiscal;
- o builder persistir dados;
- a configuração fiscal for criada automaticamente;
- o Motor de Seleção sofrer alteração não prevista.

## Resultado esperado

Ao final da PDV-05B.4B, o ERP terá uma única função oficial para transformar dados operacionais em `ContextoSelecaoFiscal`.

Essa camada será reutilizada pelo Painel Fiscal do Produto, pela Simulação Tributária e pelos futuros fluxos fiscais do PDV.
