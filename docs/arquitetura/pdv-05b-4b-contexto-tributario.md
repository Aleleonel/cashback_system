# PDV-05B.4B - Contexto Tributario

## Objetivo

Centralizar a construcao de `ContextoSelecaoFiscal`.

## Contrato oficial

Todo fluxo tributario deve chamar:

```python
construir_contexto_tributario(...)
```

O builder retorna diretamente um `ContextoSelecaoFiscal` normalizado,
validado e imutavel.

## Fontes

- regime tributario: ConfiguracaoFiscalMatriz;
- UF de origem: ConfiguracaoFiscalMatriz;
- contribuinte ICMS: valor explicito ou configuracao;
- consumidor final: valor explicito ou configuracao;
- NCM e CEST: Produto;
- UF de destino: obrigatoriamente informada pela operacao.

## Responsabilidades excluidas

O builder nao seleciona Regra Fiscal, nao calcula imposto, nao persiste dados
e nao cria configuracao fiscal automaticamente.
