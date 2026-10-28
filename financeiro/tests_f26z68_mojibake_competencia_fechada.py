from pathlib import Path
from django.test import SimpleTestCase

class F26Z68MojibakeCompetenciaFechadaTests(SimpleTestCase):
    def test_string_competencia_fechada_sem_mojibake(self):
        bad="Compet\u00c3\u00aancia fechada"
        good="Compet\u00eancia fechada"
        encontrados=[]
        for p in Path("financeiro").rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".py",".html",".txt",".js",".css"}:
                continue
            try: text=p.read_text(encoding="utf-8")
            except UnicodeDecodeError: continue
            self.assertNotIn(bad,text,str(p))
            if good in text: encontrados.append(str(p))
        self.assertTrue(encontrados,"String correta nao encontrada")