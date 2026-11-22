"""Prepara a pasta relatorio/ a partir de resultados/ e figuras/ e, se houver LaTeX, compila o PDF.

- relatorio/tabelas/*.tex   tabelas no formato do artigo (colunas escolhidas, larguras de 1 ou 2 colunas)
- relatorio/figuras/*.pdf   cópia das figuras vetoriais
- relatorio/valores.tex     macros com os números citados no texto
A pasta relatorio/ fica autocontida: para usar no Overleaf, envie-a junto com o webmedia.cls do template.

Uso:  python scripts/gerar_relatorio.py [--compilar]
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.relatorio import _celula as _celula_num, _escapar, escrever_macros  # noqa: E402


def _celula(x, casas):
    """Textos que já trazem LaTeX matemático ($...$) passam sem escape."""
    if isinstance(x, str) and "$" in x:
        return x
    return _celula_num(x, casas)

RES, FIG, REL = RAIZ / "resultados", RAIZ / "figuras", RAIZ / "relatorio"


def tabela(df: pd.DataFrame, nome: str, legenda: str, larga: bool = False, casas: int = 4,
           alinhamento: str | None = None, indice: bool = True):
    d = df.reset_index() if indice else df.copy()
    cols = [str(c) if "$" in str(c) else _escapar(str(c)) for c in d.columns]
    if indice and df.index.name is None:
        cols[0] = ""
    alin = alinhamento or "".join("r" if pd.api.types.is_numeric_dtype(d[c]) else "l" for c in d.columns)
    amb = "table*" if larga else "table"
    corpo = [" & ".join(cols) + r" \\", r"\midrule"]
    corpo += [" & ".join(_celula(x, casas) for x in row.tolist()) + r" \\" for _, row in d.iterrows()]
    tex = "\n".join([
        f"\\begin{{{amb}}}[t]", r"\centering", r"\small",
        f"\\caption{{{legenda}}}", f"\\label{{tab:{nome}}}",
        r"\begin{adjustbox}{max width=\linewidth}", f"\\begin{{tabular}}{{{alin}}}", r"\toprule",
        *corpo, r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", f"\\end{{{amb}}}", ""])
    (REL / "tabelas" / f"{nome}.tex").write_text(tex, encoding="utf-8")


def ler(nome, **kw):
    return pd.read_csv(RES / f"{nome}.csv", **kw)


def macros_extras():
    """Números adicionais citados no texto, derivados de resultados/ e data/processed/."""
    tm = ler("04_tempos_execucao", index_col=0)["media_s"]
    aj = ler("04_ajuste_complexidade", index_col=0)["r2_ajuste"]
    nm = ler("04_ajuste_n_m", index_col=0)["r2"]
    comp = ler("03_tamanho_componentes", index_col=0).iloc[:, 0]
    orig = ler("01_dados_originais", index_col=0)["valor"]
    mod = ler("09_modelos_classicos", index_col=0)
    lineares = ["BFS", "DFS", "Euler (não dirigido)", "Euler (dirigido)", "Tarjan (SCC)",
                "Tarjan (pontes e articulações)"]
    e = pd.read_csv(RAIZ / "data/processed/arestas_nao_dirigidas.csv")
    grau = pd.concat([e.src, e.dst]).value_counts()
    top = set(grau.index[: max(1, len(grau) // 100)])
    frac_top = (e.src.isin(top) | e.dst.isin(top)).mean()
    ms = lambda k: tm[k] * 1e3
    pct = lambda x: f"{100 * x:.1f}%".replace(".", ",")
    ba = [i for i in mod.index if i.startswith("Barab")][0]
    ws = [i for i in mod.index if i.startswith("Watts")][0]
    er = [i for i in mod.index if i.startswith("Erd")][0]
    return {
        "tDFS": ms("DFS"), "tEulerU": ms("Euler (não dirigido)"), "tEulerD": ms("Euler (dirigido)"),
        "tTarjan": ms("Tarjan (SCC)"), "tPontes": ms("Tarjan (pontes e articulações)"),
        "tKruskal": ms("Kruskal"), "tPrim": ms("Prim"),
        "tFWcem": ms("Floyd-Warshall (n=100)"), "tFWpuroCem": ms("Floyd-Warshall puro (n=100)"),
        "razaoFWpuro": tm["Floyd-Warshall puro (n=500)"] / tm["Floyd-Warshall (n=500)"],
        "razaoFWmil": tm["Floyd-Warshall (n=1000)"] / tm["Floyd-Warshall (n=500)"],
        "rLinMin": aj[lineares].min(), "rLinMax": aj[lineares].max(),
        "rNMmin": nm[lineares].min(), "rNMmax": nm[lineares].max(),
        "rDijkstra": aj["Dijkstra"], "rKruskal": aj["Kruskal"], "rPrim": aj["Prim"],
        "rFW": aj["Floyd-Warshall"], "rFWpuro": aj["Floyd-Warshall puro"],
        "rBF": aj["Bellman-Ford"], "rBFkm": aj["Bellman-Ford (c·k·m)"], "rBFnm": nm["Bellman-Ford"],
        "segundaComp": int(comp.index[1]), "compPares": int(comp.get(2, 0)), "compTrios": int(comp.get(3, 0)),
        "postsPorPar": float(orig["posts por par (média)"]), "postsPorParMax": int(float(orig["posts por par (máximo)"])),
        "grauMediana": float(grau.median()), "fracGrauUm": pct((grau == 1).mean()),
        "fracArestasTop": pct(frac_top),
        "Cba": mod.loc[ba, "C médio"], "Lba": mod.loc[ba, "L"], "gmaxBA": int(mod.loc[ba, "grau máx"]),
        "Cws": mod.loc[ws, "C médio"], "Lws": mod.loc[ws, "L"], "Ler": mod.loc[er, "L"],
        "gmaxER": int(mod.loc[er, "grau máx"]), "gammaBA": mod.loc[ba, "γ (MLE)"],
    }


def main():
    (REL / "tabelas").mkdir(parents=True, exist_ok=True)
    (REL / "figuras").mkdir(parents=True, exist_ok=True)
    for f in FIG.glob("*.pdf"):
        shutil.copy2(f, REL / "figuras" / f.name)
    shutil.copy2(RES / "valores.tex", REL / "valores.tex")
    escrever_macros(macros_extras(), REL / "valores_extra.tex")

    t = ler("02_tratamentos", index_col=0)
    tabela(t, "tratamento", "Tratamentos aplicados ao arquivo original.", larga=True, alinhamento="lll")

    p1 = ler("03_parte1_medidas", index_col=0)
    tabela(p1, "parte1", "Parte I: medidas estruturais e indicação do que foi calculado.", alinhamento="llll")

    alg = ler("04_resultados_algoritmos", index_col=0)
    tabela(alg, "algoritmos", "Parte II: resultados dos algoritmos no G13.", larga=True,
           alinhamento="lp{0.78\\linewidth}")

    tm = ler("04_tempos_execucao", index_col=0)
    tm = tm[["Complexidade", "Grafo", "media_s", "desvio_s", "ic_inf_s", "ic_sup_s"]].copy()
    for c in ["media_s", "desvio_s", "ic_inf_s", "ic_sup_s"]:
        tm[c] = tm[c] * 1e3
    tm.columns = ["Complexidade", "Grafo", "Média (ms)", "Desvio (ms)", "IC inf. (ms)", "IC sup. (ms)"]
    tabela(tm, "tempos", "Tempo de execução: 30 repetições, IC de 95\\% pela Normal ($z_{0{,}025}=1{,}96$).",
           larga=True, casas=4)

    aj = ler("04_ajuste_complexidade", index_col=0)
    nm = ler("04_ajuste_n_m", index_col=0)
    junto = aj.rename(columns={"c": "$c$", "r2_ajuste": "$R^2$ de $c\\cdot f$"}).join(
        nm[["r2"]].rename(columns={"r2": "$R^2$ de $an+bm$"}), how="left")
    junto.index.name = "Algoritmo"
    tabela(junto, "ajuste", "Complexidade observada: ajuste do tempo médio a $c \\cdot f(n,m)$ e a $a n + b m$.",
           casas=3)

    sw = ler("05_small_world", index_col=0)["valor"]
    swg = ler("05_small_world_graus", index_col=0)["valor"]
    tsw = pd.DataFrame({
        "G13": [sw["C(G)"], sw["L(G)"]],
        "$G(n,m)$": [sw["C_aleatorio"], sw["L_aleatorio"]],
        "G13 / $G(n,m)$": [sw["C(G)/C_aleatorio"], sw["L(G)/L_aleatorio"]],
        "mesmos graus": [swg["C_graus"], swg["L_graus"]],
        "G13 / mesmos graus": [swg["C(G)/C_graus"], swg["L(G)/L_graus"]],
    }, index=["$C$", "$L$"])
    tabela(tsw, "smallworld", "Small-world: G13 contra $G(n,m)$ e contra o nulo que preserva os graus.",
           larga=True, casas=3)

    pl = ler("06_lei_potencia", index_col=0)["valor"]
    tpl = pd.DataFrame({
        "$\\gamma$": [pl["gamma_pk"], pl["gamma_pk_bins_log"], pl["gamma_ccdf"], pl["gamma_mle"]],
        "$R^2$ / KS": [pl["r2_pk"], pl["r2_pk_bins_log"], pl["r2_ccdf"], pl["ks_mle"]],
    }, index=["Regressão em $\\log P(k)$ (bruto)", "Regressão com bins logarítmicos",
              "Regressão na CCDF", f"Máx. verossimilhança ($k_{{min}}={int(pl['kmin_mle'])}$)"])
    tabela(tpl, "potencia", "Estimativas do expoente $\\gamma$ da lei de potência.", casas=3)

    rob = ler("07_robustez", index_col=0)
    rob.columns = ["$r$", "A: $S$", "B: $c$", "C: $L$", "D: isolados"]
    tabela(rob, "robustez", "Robustez da maior componente após remover $r=\\lceil 0{,}05n \\rceil$ vértices.",
           larga=True, casas=3)

    ph = ler("08_perfil_hubs", index_col=0)
    tabela(ph, "hubs", "Perfil dos 10 subreddits de maior grau.", larga=True, casas=3)

    neg = ler("08_links_negativos", index_col=0)
    tabela(neg, "negativos", "Subreddits que mais enviam e recebem links negativos (nº de posts).", casas=3)

    mod = ler("09_modelos_classicos", index_col=0)
    mod.index.name = "Modelo"
    tabela(mod, "modelos", "G13 comparado aos modelos clássicos gerados com o mesmo $n$ e $m$ aproximado.",
           larga=True, casas=3)
    print("relatorio/ atualizado:", sorted(p.name for p in (REL / "tabelas").glob("*.tex")))

    if "--compilar" in sys.argv:
        r = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                           cwd=REL, capture_output=True, text=True)
        print(r.stdout[-1500:] if r.returncode else "PDF gerado: relatorio/main.pdf")
        if r.returncode == 0:
            shutil.copy2(REL / "main.pdf", REL / "224216276.pdf")
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
