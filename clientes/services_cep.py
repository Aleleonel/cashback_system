import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .utils import limpar_numero

def _consultar_provider(cep):
    req = Request(f"https://viacep.com.br/ws/{cep}/json/", headers={"Accept":"application/json","User-Agent":"cashback-system/1.0"})
    with urlopen(req, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))

def consultar_cep(cep):
    cep = limpar_numero(cep)
    if len(cep) != 8:
        return {"ok": False, "motivo": "cep_invalido"}
    try:
        dados = _consultar_provider(cep)
    except (OSError, HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {"ok": False, "motivo": "provider_indisponivel"}
    if not isinstance(dados, dict) or dados.get("erro"):
        return {"ok": False, "motivo": "cep_nao_encontrado"}
    return {"ok": True, "cep": cep, "endereco": {
        "logradouro": (dados.get("logradouro") or "").strip(),
        "bairro": (dados.get("bairro") or "").strip(),
        "cidade": (dados.get("localidade") or "").strip(),
        "uf": (dados.get("uf") or "").strip().upper(),
    }}