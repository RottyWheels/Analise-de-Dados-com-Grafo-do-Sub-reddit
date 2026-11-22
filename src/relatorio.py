"""Exportação de tabelas (CSV + LaTeX em português) e figuras (PNG + PDF)."""
from __future__ import annotations

import numbers
from pathlib import Path

import numpy as np

import pandas as pd

RES = Path("resultados")
FIG = Path("figuras")


def _fmt_num(x, casas: int = 4):
    """Número em formato brasileiro: vírgula decimal, ponto de milhar; notação científica
    (com vírgula) para valores muito pequenos ou grandes não inteiros."""
    if isinstance(x, (bool, np.bool_)):
        return "sim" if x else "não"
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    if isinstance(x, numbers.Integral) or (isinstance(x, float) and x.is_integer() and abs(x) < 1e15):
        return f"{int(x):,}".replace(",", ".")
    if isinstance(x, float):
        if x != 0 and (abs(x) < 1e-3 or abs(x) >= 1e7):
            m, e = f"{x:.{casas - 1}e}".split("e")
            return f"${m.replace('.', ',')} \\times 10^{{{int(e)}}}$"
        if abs(x) >= 1000:
            return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{x:.{casas}g}".replace(".", ",")
    return x


def _escapar(s: str) -> str:
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")]:
        s = s.replace(a, b)
    return s


def _celula(x, casas):
    v = _fmt_num(x, casas)
    if isinstance(v, str) and v.startswith("$"):
        return v
    return _escapar(str(v))


def tabela_latex(df: pd.DataFrame, legenda: str, rotulo: str, casas: int = 4,
                 indice: bool = True) -> str:
    """Tabela LaTeX (booktabs) com vírgula decimal, \\caption e \\label."""
    d = df.reset_index() if indice else df.copy()
    cols = [str(c) for c in d.columns]
    if indice and df.index.name is None:
        cols[0] = ""
    alin = "".join("r" if pd.api.types.is_numeric_dtype(d[c]) else "l" for c in d.columns)
    linhas = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        f"\\caption{{{legenda}}}", f"\\label{{{rotulo}}}",
        f"\\begin{{tabular}}{{{alin}}}", r"\toprule",
        " & ".join(_escapar(c) for c in cols) + r" \\", r"\midrule",
    ]
    for _, row in d.iterrows():
        linhas.append(" & ".join(_celula(x, casas) for x in row.tolist()) + r" \\")
    linhas += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(linhas) + "\n"


def salvar_tabela(df: pd.DataFrame, nome: str, legenda: str, casas: int = 4,
                  indice: bool = True, pasta: Path = RES) -> pd.DataFrame:
    """Grava resultados/<nome>.csv e resultados/<nome>.tex (rótulo tab:<nome>)."""
    pasta.mkdir(parents=True, exist_ok=True)
    df.to_csv(pasta / f"{nome}.csv", index=indice)
    (pasta / f"{nome}.tex").write_text(
        tabela_latex(df, legenda, f"tab:{nome}", casas, indice), encoding="utf-8")
    return df


def salvar_figura(fig, nome: str, pasta: Path = FIG):
    """Grava figuras/<nome>.png (200 dpi) e figuras/<nome>.pdf (vetorial, para o LaTeX)."""
    pasta.mkdir(parents=True, exist_ok=True)
    fig.savefig(pasta / f"{nome}.png", dpi=200, bbox_inches="tight")
    fig.savefig(pasta / f"{nome}.pdf", bbox_inches="tight")
    return fig


def _macro_valor(v, casas: int = 3) -> str:
    v = _fmt_num(v, casas)
    return v if isinstance(v, str) else str(v)


def escrever_macros(valores: dict, caminho: Path = RES / "valores.tex", casas: int = 3) -> Path:
    """Grava \\newcommand{\\nome}{valor} para cada item, com números no formato brasileiro.
    Nomes de macro LaTeX só aceitam letras: use chaves como 'diametro', 'gammaMLE'."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = ["% Gerado por src/relatorio.py (escrever_macros). Não editar à mão."]
    for nome, v in valores.items():
        if not nome.isalpha():
            raise ValueError(f"nome de macro inválido: {nome}")
        val = v if isinstance(v, str) else _macro_valor(v, casas)
        linhas.append(f"\\newcommand{{\\{nome}}}{{{val}}}")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho
