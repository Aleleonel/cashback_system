"""Autorizacao interna e temporaria para estorno atomico de repasse de adquirente."""
from contextlib import contextmanager
from contextvars import ContextVar

_autorizado = ContextVar("financeiro_estorno_repasse_autorizado", default=False)

@contextmanager
def autorizar_estorno_repasse():
    token = _autorizado.set(True)
    try:
        yield
    finally:
        _autorizado.reset(token)

def estorno_repasse_autorizado():
    return _autorizado.get()


_registro_autorizado = ContextVar("financeiro_registro_repasse_autorizado", default=False)


@contextmanager
def autorizar_registro_repasse():
    token = _registro_autorizado.set(True)
    try:
        yield
    finally:
        _registro_autorizado.reset(token)


def registro_repasse_autorizado():
    return _registro_autorizado.get()
