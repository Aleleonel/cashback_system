from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SKIP={".git","venv",".venv","node_modules","staticfiles","diagnostico","diagnosticos","__pycache__"}
EXTS={".py",".html",".css",".js",".json",".md",".yml",".yaml",".toml",".ini",".cfg",".ps1"}
MARKERS=("ÃƒÆ’","Ãƒâ€š","Ã¢â‚¬â„¢","Ã¢â‚¬Å“","Ã¢â‚¬Â","Ã¢â‚¬â€œ","Ã¢â‚¬â€","â”œ","â”¬","ï¿½")
errors=[]
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in EXTS: continue
    if any(x in SKIP for x in p.relative_to(ROOT).parts): continue
    if p.resolve() == Path(__file__).resolve(): continue
    b=p.read_bytes()
    try: t=b.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        errors.append(f"UTF8_INVALIDO|{p.relative_to(ROOT)}|{e}");continue
    for n,line in enumerate(t.splitlines(),1):
        hit=next((m for m in MARKERS if m in line),None)
        if hit: errors.append(f"MOJIBAKE|{p.relative_to(ROOT)}|L{n}|{hit}|{line[:180]}")
if errors:
    print("ENCODING_GUARD=FALHA")
    for item in errors:
        print(item.encode("ascii","backslashreplace").decode("ascii"))
    raise SystemExit(1)
print("ENCODING_GUARD=OK")