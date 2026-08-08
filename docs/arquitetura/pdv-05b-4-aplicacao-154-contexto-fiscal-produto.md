# PDV-05B.4 — Projeto da Aplicação 154

## Título

Integração do Contexto Fiscal na tela de detalhe do Produto

## Objetivo

Preparar a view de detalhe do Produto para consumir a camada fiscal já criada, sem alterar a interface visual nesta etapa.

A Aplicação 154 deverá construir um `ContextoSelecaoFiscal`, chamar `resolver_produto_fiscal()` uma única vez e disponibilizar o resultado ao template por meio da variável `produto_fiscal`.

## Branch obrigatória

```text
feature/pdv-05b-4-motor-tributario-produto
```

A aplicação deve ser interrompida caso a branch atual seja diferente.

## Arquivo que será alterado

```text
produtos/views/produtos.py
```

## Função que será alterada

```python
detalhe_produto(request, produto_id)
```

## Estado atual

A view já:

- utiliza `get_contexto_operacional_usuario(request.user)`;
- obtém a matriz do contexto operacional;
- recupera o Produto por selector;
- renderiza `produtos/produtos/detalhe.html`;
- envia `produto` ao template.

## Estado esperado após a aplicação

A view deverá:

1. obter o contexto operacional existente;
2. recuperar o Produto normalmente;
3. montar um `ContextoSelecaoFiscal` apenas com dados reais;
4. chamar `resolver_produto_fiscal()` uma única vez;
5. adicionar `produto_fiscal` ao contexto do template;
6. preservar o comportamento atual da tela.

## Imports previstos

A view deverá importar:

```python
from datetime import date

from fiscal.domain.selecao_fiscal import ContextoSelecaoFiscal
from produtos.services.fiscal import resolver_produto_fiscal
```

Os imports finais deverão respeitar o padrão já utilizado no arquivo.

## Construção do contexto fiscal

O contexto deverá utilizar somente valores disponíveis no sistema.

Campos previstos:

```python
ContextoSelecaoFiscal(
    data_operacao=date.today(),
    regime_tributario=...,
    tipo_operacao="saida",
    finalidade_operacao="venda",
    uf_origem=...,
    uf_destino=...,
    matriz=contexto["matriz"],
    loja=contexto.get("loja"),
    contribuinte_icms=None,
    consumidor_final=None,
    ncm=None,
    cest=None,
)
```

## Regra de segurança

Nenhum valor material deve ser inventado.

Se `regime_tributario`, `uf_origem` ou `uf_destino` não puderem ser obtidos com segurança, a aplicação deverá:

- usar um helper explícito;
- retornar contexto incompleto de forma controlada;
- permitir que o resolvedor produza status e alertas;
- nunca gerar erro 500 por ausência de configuração.

## Origem dos dados

A aplicação deverá validar antes de gravar:

- como o regime tributário é representado no sistema;
- de onde vem a UF da matriz ou loja;
- qual UF deve ser utilizada como destino no detalhe do Produto;
- se existe configuração fiscal padrão por matriz ou loja.

Caso o projeto não possua origem confiável para algum desses dados, isso deverá ser tratado como contexto incompleto, não como valor padrão arbitrário.

## Contrato com o resolvedor

A chamada deverá ocorrer uma única vez:

```python
produto_fiscal = resolver_produto_fiscal(
    produto=produto,
    contexto=contexto_fiscal,
)
```

O resultado deverá ser enviado ao template:

```python
return render(
    request,
    "produtos/produtos/detalhe.html",
    {
        "produto": produto,
        "produto_fiscal": produto_fiscal,
    },
)
```

## O que entra nesta aplicação

- integração da view com `ContextoSelecaoFiscal`;
- chamada ao `resolver_produto_fiscal`;
- inclusão de `produto_fiscal` no contexto do template;
- testes da view;
- tratamento controlado de contexto incompleto;
- atualização da documentação técnica.

## O que não entra nesta aplicação

- alteração visual no template;
- criação do painel fiscal;
- botão de simulação;
- modal;
- AJAX;
- nova rota;
- cálculo monetário;
- persistência de simulação;
- alteração de models;
- migration;
- alteração no Motor de Seleção;
- alteração no Motor Tributário;
- commit automático.

## Testes obrigatórios

A Aplicação 154 deverá criar ou atualizar testes para garantir:

1. a view continua acessível;
2. `resolver_produto_fiscal()` é chamado uma única vez;
3. o Produto correto é enviado ao resolvedor;
4. o contexto fiscal é montado com matriz e loja corretas;
5. `produto_fiscal` é enviado ao template;
6. contexto incompleto não gera erro 500;
7. permissões atuais continuam sendo respeitadas;
8. o template atual continua renderizando;
9. nenhuma migration é criada;
10. os testes anteriores continuam passando.

## Validações obrigatórias

Após a aplicação:

```powershell
python manage.py check
```

```powershell
python manage.py makemigrations --check --dry-run
```

```powershell
python manage.py test produtos.tests fiscal.tests.test_motor_selecao_regra_fiscal --verbosity=1
```

## Critérios de sucesso

A aplicação será considerada aprovada quando:

- a branch estiver correta;
- a view importar os contratos fiscais sem erro;
- o resolvedor for chamado uma única vez;
- `produto_fiscal` chegar ao template;
- a tela permanecer visualmente inalterada;
- os testes passarem;
- nenhuma migration for criada;
- o `git diff` mostrar apenas alterações previstas;
- nenhum commit automático for realizado.

## Critérios de rollback

O rollback deverá ocorrer automaticamente caso:

- a branch esteja incorreta;
- algum arquivo obrigatório não exista;
- a alteração provoque erro de sintaxe;
- `manage.py check` falhe;
- surja migration inesperada;
- qualquer teste obrigatório falhe;
- a view deixe de renderizar;
- o contexto fiscal provoque erro não tratado.

## Arquivos previstos

```text
produtos/views/produtos.py
produtos/tests/test_produto_fiscal_detalhe.py
docs/arquitetura/pdv-05b-4-aplicacao-154-contexto-fiscal-produto.md
```

## Resultado esperado

Após a Aplicação 154, a tela de detalhe do Produto continuará visualmente igual, porém o template passará a receber:

```python
produto_fiscal
```

Esse objeto será utilizado na Aplicação 156 para montar o painel **Classificação Fiscal Efetiva**.
