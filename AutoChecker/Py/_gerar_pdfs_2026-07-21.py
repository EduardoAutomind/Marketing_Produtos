# -*- coding: utf-8 -*-
"""Gera os PDFs dos dois estudos de 21/07/2026 (marca AutoMind via _obs_lib/pdf.py)."""
import sys
from pathlib import Path

RAIZ = Path(r"C:\Projetos\Observabilidade")
sys.path.insert(0, str(RAIZ / ".claude" / "skills" / "_obs_lib"))
import pdf  # noqa: E402

BASE = RAIZ / "Cronograma observabilidade" / "AutoChecker"
MD, PDF = BASE / "Md", BASE / "Pdf"

DOCS = [
    dict(
        slug="Guia_Funcionamento_BaseCompartilhada_AutoChecker_2026-07-21",
        titulo="Como o AutoChecker funciona",
        subtitulo="Guia de produto para o time de marketing — Base Compartilhada",
        eyebrow="AutoChecker · Automind",
        rodape="Elaborado em 21/07/2026 · Fonte: documentação oficial do produto (REV. 01, 21/07/2026) · Uso interno",
    ),
    dict(
        slug="Analise_Integracao_AutoLoad_AutoChecker_2026-07-21",
        titulo="Integração AutoLoad ↔ AutoChecker",
        subtitulo="Análise técnica do contrato, da autenticação e da cobertura de observabilidade",
        eyebrow="Observabilidade · Automind",
        rodape="Elaborado em 21/07/2026 · Fontes: documentação oficial de ambos os produtos (REV. 01) e Sentry org automind-qd (janela de 30 dias)",
    ),
]

for d in DOCS:
    md_path = MD / f"{d['slug']}.md"
    if not md_path.exists():
        print(f"FALTA: {md_path}")
        continue
    res = pdf.gerar(
        md_path.read_text(encoding="utf-8"),
        PDF / f"{d['slug']}.pdf",
        titulo=d["titulo"], subtitulo=d["subtitulo"],
        eyebrow=d["eyebrow"], rodape=d["rodape"],
    )
    print(f"{d['slug']}: {res}")
