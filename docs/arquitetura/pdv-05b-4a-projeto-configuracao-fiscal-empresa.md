# PDV-05B.4A — Projeto 156

## Título

Configuração Fiscal Oficial por Matriz

## Objetivo

Criar uma fonte oficial, única e reutilizável para os parâmetros fiscais operacionais da empresa.

A nova configuração deverá fornecer os dados necessários para construir o `ContextoSelecaoFiscal` sem inferências, valores arbitrários ou dependência de regras fiscais cadastradas.

## Branch obrigatória

```text
feature/pdv-05b-4-motor-tributario-produto
```

Nenhuma alteração poderá ser aplicada em `master` ou `develop`.

## Entidade proposta

```python
ConfiguracaoFiscalMatriz
```

## Aplicativo recomendado

```text
fiscal
```

### Justificativa

A entidade pertence ao domínio fiscal, embora tenha relação direta com a `Matriz`.

Ela não deve ser colocada em:

- `produtos`, porque não é configuração do Produto;
- `core`, porque não é configuração genérica do sistema;
- `configuracoes`, porque esse app funciona como central de navegação e orquestração;
- `empresas`, porque os campos e validações pertencem ao domínio tributário.

O app `fiscal` já possui:

- regimes tributários;
- validação de UF;
- regras fiscais;
- benefícios fiscais;
- Motor de Seleção;
- permissões fiscais;
- serviços e formulários do domínio.

## Relacionamento

```python
matriz = models.OneToOneField(
    Matriz,
    on_delete=models.PROTECT,
    related_name="configuracao_fiscal",
)
```

## Decisão sobre exclusão

O relacionamento deverá usar:

```python
on_delete=models.PROTECT
```

A configuração fiscal representa histórico e integridade operacional. A exclusão de uma Matriz que possua configuração fiscal deverá ser impedida.

## Campos mínimos

### Matriz

```python
matriz
```

- relacionamento `OneToOne`;
- obrigatório;
- uma configuração fiscal por Matriz;
- não editável após criação pelo fluxo comum.

### Regime tributário

```python
regime_tributario
```

Valores reutilizados do domínio fiscal:

```text
normal
simples
mei
```

Não deverão ser duplicados `choices`.

A implementação deverá reutilizar:

```python
RegraFiscal.REGIME_TRIBUTARIO_CHOICES
```

ou extrair as constantes para um contrato compartilhado, caso a validação 157 conclua que isso reduz acoplamento.

### UF de origem

```python
uf_origem
```

- `CharField(max_length=2)`;
- obrigatória;
- normalizada para letras maiúsculas;
- validada com o mesmo conjunto de UFs do domínio fiscal;
- não deve aceitar valor fora das UFs brasileiras válidas.

A normalização deverá reutilizar:

```python
RegraFiscal.normalizar_uf
```

ou um helper fiscal compartilhado aprovado na validação 157.

### Indicador de contribuinte do ICMS

```python
contribuinte_icms
```

- `BooleanField`;
- obrigatório;
- representa o padrão operacional da própria Matriz;
- não representa o destinatário de cada venda.

### Consumidor final padrão

```python
consumidor_final_padrao
```

- `BooleanField`;
- obrigatório;
- serve como valor padrão para operações sem destinatário definido;
- poderá ser sobrescrito por contexto de venda real no futuro.

### Ativa

```python
ativa
```

- `BooleanField(default=True)`;
- indica se a configuração pode ser utilizada;
- configuração inativa permanece disponível para histórico;
- uma configuração inativa não deve ser utilizada para novas resoluções fiscais.

### Observações

```python
observacoes
```

- `TextField(blank=True)`;
- apenas informação administrativa;
- não participa do Motor de Seleção.

### Auditoria temporal

```python
criado_em
atualizado_em
```

- `DateTimeField(auto_now_add=True)`;
- `DateTimeField(auto_now=True)`.

## Campos que não entram nesta etapa

Ficam fora do escopo da PDV-05B.4A:

- inscrição estadual;
- inscrição municipal;
- CRT separado;
- CNAE;
- código de município IBGE;
- certificado digital;
- senha de certificado;
- CSC;
- token;
- ambiente de homologação ou produção;
- série fiscal;
- numeração de NF-e ou NFC-e;
- modelo de documento fiscal;
- contingência;
- emissão fiscal;
- cálculo monetário de tributos;
- configuração específica por Loja.

## Regras de negócio

### Unicidade

Cada Matriz poderá possuir no máximo uma `ConfiguracaoFiscalMatriz`.

A unicidade será garantida pelo `OneToOneField`.

### Ativação

Uma configuração deverá estar ativa para participar de novas resoluções.

### Histórico

Configurações inativas não serão excluídas automaticamente.

### Regime tributário

O regime deverá ser um dos valores aceitos pelo domínio fiscal.

### Compatibilidade com ICMS

Regras iniciais:

- regime `normal` utiliza CST ICMS;
- regimes `simples` e `mei` utilizam CSOSN;
- esta entidade não armazenará CST ou CSOSN;
- ela apenas informa o regime operacional da Matriz.

### UF

A UF será normalizada antes da validação e persistência.

### Valores padrão

Nenhum valor fiscal deverá ser criado silenciosamente.

Não será permitido:

```python
regime_tributario="normal"
uf_origem="SP"
```

como default automático de migration ou model.

O usuário deverá configurar esses valores explicitamente.

## Estado inicial após migration

A migration criará apenas a tabela.

Ela não deverá criar configurações fiscais automaticamente para Matrizes existentes.

Isso evita:

- inferir regime tributário;
- inferir UF;
- criar dados incorretos;
- mascarar empresas sem configuração.

## Comportamento sem configuração

Quando uma Matriz não possuir configuração fiscal ativa:

- o sistema não deverá gerar erro 500;
- a resolução fiscal deverá retornar contexto incompleto;
- o painel futuro deverá informar que a configuração fiscal da empresa está pendente;
- a simulação tributária deverá ser bloqueada ou solicitar configuração.

## Selector proposto

Arquivo:

```text
fiscal/selectors_configuracao_fiscal.py
```

Contrato:

```python
def get_configuracao_fiscal_matriz(*, matriz):
    ...
```

Comportamento:

- retorna a configuração ativa;
- retorna `None` quando não existir;
- não cria registros;
- não altera estado;
- utiliza `select_related("matriz")` quando necessário.

## Service proposto

Arquivo:

```text
fiscal/services_configuracao_fiscal.py
```

Contratos iniciais:

```python
def criar_configuracao_fiscal_matriz(
    *,
    matriz,
    dados,
    usuario_executor,
    request=None,
):
    ...
```

```python
def atualizar_configuracao_fiscal_matriz(
    *,
    configuracao,
    dados,
    usuario_executor,
    request=None,
):
    ...
```

Responsabilidades:

- validar dados;
- normalizar UF;
- impedir duplicidade;
- executar `full_clean()`;
- salvar dentro de transação;
- registrar auditoria;
- não montar contexto fiscal;
- não chamar Motor de Seleção.

## Form proposto

Arquivo:

```text
fiscal/forms_configuracao_fiscal.py
```

Classe:

```python
ConfiguracaoFiscalMatrizForm
```

Campos:

```text
regime_tributario
uf_origem
contribuinte_icms
consumidor_final_padrao
ativa
observacoes
```

A Matriz não deverá ser escolhida manualmente pelo formulário comum. Ela virá do contexto operacional.

## Permissão

Permissão existente a reutilizar:

```python
PERMISSAO_FISCAL_CONFIGURAR
```

Não será criada nova permissão nesta etapa, salvo se a validação 157 identificar conflito real.

## Auditoria

A criação e alteração deverão registrar:

```python
registrar_auditoria(...)
```

Com:

- usuário executor;
- Matriz;
- Loja do contexto, quando disponível;
- ação de criar ou editar;
- recurso `ConfiguracaoFiscalMatriz`;
- identificador do registro;
- request, quando disponível.

## Admin

A entidade poderá ser registrada no Django Admin para suporte técnico.

O Admin não substituirá a futura interface oficial.

Configuração recomendada:

- `list_display`;
- filtros por regime, UF e ativa;
- busca por nome e CNPJ da Matriz;
- `readonly_fields` para datas;
- proteção do relacionamento com Matriz.

## Migration planejada

A nova entidade exigirá migration justificada.

Nome esperado aproximado:

```text
fiscal/migrations/0023_configuracao_fiscal_matriz.py
```

O número real dependerá do estado atual das migrations.

A migration deverá conter apenas:

- criação da tabela;
- relacionamento com Matriz;
- campos definidos;
- índices necessários;
- nenhuma carga automática de dados.

## Índices

O `OneToOneField` já criará unicidade e índice para Matriz.

Índice adicional candidato:

```python
models.Index(
    fields=["ativa", "regime_tributario"],
    name="fiscal_cfg_ativa_reg_idx",
)
```

A validação 157 deverá confirmar se esse índice é útil nesta fase. Como haverá apenas uma configuração por Matriz, ele poderá ser dispensado para evitar otimização prematura.

## Meta proposta

```python
class Meta:
    verbose_name = "Configuração fiscal da matriz"
    verbose_name_plural = "Configurações fiscais das matrizes"
    ordering = ("matriz__nome",)
```

Não será criada constraint adicional de unicidade, pois o `OneToOneField` já garante o contrato.

## Representação textual

```python
def __str__(self):
    return f"Configuração fiscal - {self.matriz.nome}"
```

## Método de normalização

A normalização deverá ocorrer antes de `full_clean()`:

```python
def clean(self):
    self.uf_origem = RegraFiscal.normalizar_uf(self.uf_origem)
    ...
```

O model não deverá duplicar a lista de UFs válidas.

## Método de estado

Propriedade candidata:

```python
@property
def pronta_para_operacao(self):
    ...
```

Critérios iniciais:

- ativa;
- regime tributário válido;
- UF de origem válida.

A propriedade não deverá consultar banco nem executar Motor de Seleção.

## Contrato com o contexto fiscal

A entidade será consumida futuramente por um serviço separado:

```python
construir_contexto_fiscal_operacional(...)
```

A `ConfiguracaoFiscalMatriz` não deverá importar:

- Produto;
- Regra Fiscal selecionada;
- Motor de Seleção;
- DTO do Produto.

A direção correta da dependência será:

```text
ConfiguracaoFiscalMatriz
        ↓
Construtor de contexto
        ↓
ContextoSelecaoFiscal
        ↓
Motor de Seleção
        ↓
Resolver do Produto
```

## Arquivos previstos para a Aplicação 158

```text
fiscal/models_configuracao_fiscal.py
fiscal/forms_configuracao_fiscal.py
fiscal/selectors_configuracao_fiscal.py
fiscal/services_configuracao_fiscal.py
fiscal/admin.py
fiscal/tests/test_configuracao_fiscal_matriz.py
fiscal/migrations/00XX_configuracao_fiscal_matriz.py
docs/arquitetura/pdv-05b-4a-configuracao-fiscal-empresa.md
docs/usabilidade/fiscal/configuracao-fiscal-empresa.md
```

Também poderá ser necessário ajustar:

```text
fiscal/models.py
```

ou os exports do app, dependendo do padrão atual do módulo fiscal.

## Testes obrigatórios

### Model

1. cria configuração válida;
2. impede duas configurações para a mesma Matriz;
3. normaliza UF;
4. rejeita UF inválida;
5. rejeita regime inválido;
6. preserva configuração inativa;
7. protege a Matriz contra exclusão;
8. representa o registro corretamente;
9. calcula `pronta_para_operacao`.

### Selector

1. retorna configuração ativa;
2. retorna `None` quando ausente;
3. ignora configuração inativa;
4. não cria registro.

### Service

1. cria configuração;
2. impede duplicidade;
3. atualiza configuração;
4. chama `full_clean`;
5. registra auditoria;
6. respeita transação;
7. não altera Matriz;
8. não executa Motor de Seleção.

### Regressão

Devem continuar passando:

```text
fiscal.tests.test_motor_selecao_regra_fiscal
fiscal.tests.test_regra_fiscal
produtos.tests.services.fiscal.test_resolver_produto_fiscal
produtos.tests.test_produto_fiscal_model
```

## Validação pré-migration — Projeto 157

Antes da aplicação, o próximo diagnóstico deverá confirmar:

1. padrão real de organização dos models do app `fiscal`;
2. número atual da última migration;
3. imports permitidos sem ciclo;
4. assinatura real de `registrar_auditoria`;
5. ações disponíveis em `RegistroAuditoria`;
6. padrão real dos services transacionais;
7. padrão de testes de models fiscais;
8. se `RegraFiscal.REGIME_TRIBUTARIO_CHOICES` pode ser reutilizado sem acoplamento circular;
9. se `RegraFiscal.normalizar_uf` pode ser reutilizado;
10. se será necessário extrair constantes compartilhadas;
11. nomes de related names já utilizados;
12. ausência de `ConfiguracaoFiscalMatriz` ou equivalente já existente.

## Critérios de sucesso da aplicação futura

A Aplicação 158 será aprovada quando:

- a migration for criada exatamente como planejado;
- `manage.py check` passar;
- `makemigrations --check --dry-run` não detectar alterações após a migration;
- todos os testes novos passarem;
- regressões fiscais e de Produto passarem;
- nenhuma configuração for criada automaticamente;
- nenhuma Matriz existente for alterada;
- nenhuma tela atual quebrar;
- o Git mostrar apenas alterações previstas;
- nenhum commit automático for realizado.

## Critérios de rollback

Rollback automático se:

- a branch estiver incorreta;
- já existir entidade equivalente;
- surgir ciclo de importação;
- a migration incluir alterações não planejadas;
- houver default fiscal inventado;
- o `manage.py check` falhar;
- qualquer teste falhar;
- a migration alterar dados existentes;
- a auditoria não puder ser registrada corretamente.

## Decisão arquitetural

A configuração fiscal oficial ficará no domínio `fiscal`, relacionada 1:1 com a `Matriz`.

A Central de Configurações poderá expor essa funcionalidade visualmente no futuro, mas não será dona do model.

Essa decisão preserva:

- coesão do domínio;
- fonte única de verdade;
- reutilização no PDV, compras, documentos fiscais e Produto;
- separação entre configuração comercial e fiscal;
- evolução futura sem retrabalho.
