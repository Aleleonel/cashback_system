from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXTS = {".py",".html",".htm",".js",".css",".json",".md",".yml",".yaml",".toml",".ini",".cfg"}
SKIP_DIRS = {".git","venv",".venv","node_modules","staticfiles","media","diagnostico","diagnosticos","__pycache__"}

def u(*codes: int) -> str:
    return "".join(chr(c) for c in codes)

MARKERS = (
    u(195,161),u(195,162),u(195,163),u(195,164),u(195,165),
    u(195,167),u(195,169),u(195,170),u(195,173),u(195,179),
    u(195,180),u(195,181),u(195,186),u(195,188),
    u(226,8364,339),u(226,8364,8220),u(226,8364,8221),u(226,8364,8226),
    chr(0xFFFD),
)

# Ocorrencias deliberadas usadas por testes de deteccao.
ALLOW_FILES = {
    "compras/tests/test_ui_recebimento_devolucao.py",
    "configuracoes/tests/test_formas_pagamento_ui_r20.py",
}

def candidates():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield p, rel.as_posix()

invalid = []
bad = []
allowed = []

for path, rel in candidates():
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        invalid.append((rel, str(exc)))
        continue
    for no, line in enumerate(text.splitlines(), 1):
        if not any(marker in line for marker in MARKERS):
            continue
        item = (rel, no, line.strip())
        if rel in ALLOW_FILES:
            allowed.append(item)
        else:
            bad.append(item)

print(f"UTF8_INVALIDOS={len(invalid)}")
for rel, err in invalid:
    print(f"UTF8_INVALIDO|{rel}|{err}".encode("ascii","backslashreplace").decode("ascii"))
print(f"MOJIBAKE_REAL_NAO_PERMITIDO={len(bad)}")
for rel, no, line in bad:
    print(f"NAO_PERMITIDO|{rel}|L{no}|{line}".encode("ascii","backslashreplace").decode("ascii"))
print(f"OCORRENCIAS_INTENCIONAIS={len(allowed)}")
for rel, no, line in allowed:
    print(f"INTENCIONAL|{rel}|L{no}|{line}".encode("ascii","backslashreplace").decode("ascii"))

if invalid or bad:
    print("ENCODING_GUARD=REPROVADO")
    sys.exit(1)
print("ENCODING_GUARD=APROVADO")
sys.exit(0)