# PDV-04 — Plano de Consolidação

## Constatação corrigida

A suíte central executou 63 testes e apresentou cinco falhas. O `manage.py check`
passou sem problemas.

As cinco falhas são testes estruturais que procuram diretamente em
`fechamento.py`:

- `UsoVoucher.objects.create(...)`;
- `Voucher.objects`;
- `select_for_update()`;
- validação direta de `limite_utilizacao`.

A arquitetura atual indica delegação:

```text
fechamento.py
    -> beneficios.py
        -> vouchers/services/utilizacao.py
```

A primeira entrega não deve reintroduzir regras de voucher no fechamento.
Deve confirmar a delegação e corrigir contratos antigos.

## Entrega 04A

1. Diagnosticar a localização real das regras.
2. Executar testes funcionais do adapter e do serviço oficial.
3. Confirmar bloqueio, limite global e registro do uso.
4. Atualizar somente testes estruturais obsoletos.
5. Reexecutar a suíte central.
6. Registrar documentação, homologação e changelog.

## Regra arquitetural

`fechamento.py` deve orquestrar, não implementar regras internas de voucher.
