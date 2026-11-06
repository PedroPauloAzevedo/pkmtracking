"""
Testes estruturais da Skill: as referências da base de conhecimento continuam valendo?
  1. Toda referência `arquivo::nome` em knowledge/KNOWN_METHODS.md existe (def, classe ou constante no arquivo).
  2. Todo arquivo citado (`tracker/...`, `testes/...`, `experiments/...`, `tools/...`, `PROJECT_KNOWLEDGE/...`) existe.
  3. O SKILL.md tem nome e descrição e aponta só para arquivos que existem.
  4. Nenhum arquivo da Skill contém caminhos do computador do Pedro ou nicks (o repositório é público).
Uso:  python -I .claude/skills/statistical-analyst/tests/test_referencias.py   (a partir da raiz do projeto ou de qualquer lugar)
"""
import re
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RAIZ = SKILL.parent.parent.parent  # .claude/skills/<skill> -> projeto


def _resolver(caminho: str) -> Path:
    for base in (RAIZ, SKILL, RAIZ / "testes" / "experimentos", RAIZ / "PROJECT_KNOWLEDGE" / "03_DECISIONS"):
        if (base / caminho).exists():
            return base / caminho
    return RAIZ / caminho


class Referencias(unittest.TestCase):
    def test_funcoes_citadas_existem(self):
        texto = (SKILL / "knowledge" / "KNOWN_METHODS.md").read_text(encoding="utf-8")
        refs = re.findall(r"`([\w./-]+\.py)::(\w+)`", texto)
        self.assertGreater(len(refs), 40)
        faltando = []
        for arq, nome in refs:
            p = _resolver(arq)
            if not p.exists():
                faltando.append(f"{arq} (arquivo)")
                continue
            codigo = p.read_text(encoding="utf-8")
            if not re.search(rf"^\s*(def|class)\s+{nome}\b|^{nome}\s*=|^\s*{nome}\s*[:=]", codigo, re.M):
                faltando.append(f"{arq}::{nome}")
        self.assertEqual(faltando, [], f"referências quebradas: {faltando}")

    def test_arquivos_citados_existem(self):
        faltando = []
        for md in list((SKILL / "knowledge").glob("*.md")) + [SKILL / "SKILL.md", SKILL / "experiments" / "README.md"]:
            for c in re.findall(r"`((?:tracker|testes|experiments|tools|knowledge|tests|PROJECT_KNOWLEDGE|docs)/[\w./-]+\.(?:py|md|json))`",
                                md.read_text(encoding="utf-8")):
                if not _resolver(c).exists():
                    faltando.append(f"{md.name}: {c}")
        self.assertEqual(faltando, [], f"arquivos citados que não existem: {faltando}")

    def test_skill_md(self):
        t = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cab = re.match(r"---\n(.*?)\n---\n", t, re.S)
        self.assertIsNotNone(cab)
        self.assertRegex(cab.group(1), r"(?m)^name: statistical-analyst$")
        self.assertRegex(cab.group(1), r"(?m)^description: .{200,}")
        self.assertLess(len(t.splitlines()), 500)

    def test_sem_dados_privados(self):
        proibidos = re.compile(r"(?i)peponildo|acellerat|_out_|C:\\Users|\\ctcg|C:/ctcg|/c/ctcg|Meu Drive|@gmail")
        achados = []
        for p in SKILL.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".py", ".json", ".yaml") and p.name != Path(__file__).name:
                if proibidos.search(p.read_text(encoding="utf-8", errors="ignore")):
                    achados.append(str(p.relative_to(SKILL)))
        self.assertEqual(achados, [], f"dados privados em: {achados}")


if __name__ == "__main__":
    r = unittest.main(exit=False, verbosity=1).result
    print("OK" if r.wasSuccessful() else "FALHOU")
    sys.exit(0 if r.wasSuccessful() else 1)
