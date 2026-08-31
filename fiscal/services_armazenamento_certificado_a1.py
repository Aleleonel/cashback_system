from __future__ import annotations
import os,tempfile,uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from fiscal.services_certificado_a1 import carregar_certificado_a1
EXTENSOES_A1={'.pfx','.p12'}
TAMANHO_MAXIMO_A1=5*1024*1024
def diretorio_privado_certificados_a1():
    valor=str(os.environ.get('PROCASH_CERTIFICADOS_A1_DIR','') or '').strip()
    return Path(valor).expanduser().resolve() if valor else (Path(settings.BASE_DIR)/'certificados').resolve()
def armazenar_certificado_a1(*,loja_id,arquivo,senha):
    if arquivo is None: raise ValidationError('Selecione um certificado A1.')
    if not str(senha or ''): raise ValidationError('Informe a senha do certificado A1.')
    ext=Path(str(getattr(arquivo,'name','') or '')).suffix.lower()
    if ext not in EXTENSOES_A1: raise ValidationError('Use um arquivo .pfx ou .p12.')
    tamanho=int(getattr(arquivo,'size',0) or 0)
    if tamanho<=0 or tamanho>TAMANHO_MAXIMO_A1: raise ValidationError('Tamanho de certificado A1 invalido.')
    base=diretorio_privado_certificados_a1(); base.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='procash_a1_',suffix=ext); os.close(fd); tmp=Path(tmp)
    destino=base/f'loja_{int(loja_id)}_{uuid.uuid4().hex}{ext}'
    try:
        with tmp.open('wb') as out:
            for chunk in arquivo.chunks(): out.write(chunk)
        carregar_certificado_a1(referencia=str(tmp), senha=str(senha))
        with destino.open('xb') as out: out.write(tmp.read_bytes())
        try: os.chmod(destino,0o600)
        except OSError: pass
    except Exception:
        if destino.exists(): destino.unlink()
        raise
    finally:
        if tmp.exists(): tmp.unlink()
    return str(destino)
def remover_certificado_a1_por_referencia(referencia):
    referencia=str(referencia or '').strip()
    if not referencia: return
    base=diretorio_privado_certificados_a1(); alvo=Path(referencia).expanduser().resolve()
    try: alvo.relative_to(base)
    except ValueError as exc: raise ValidationError('Referencia A1 fora do armazenamento privado.') from exc
    if alvo.is_file(): alvo.unlink()
