import math

import pandas as pd

from src import robustez as R, tratamento as T, algoritmos as A
from src.relatorio import tabela_latex, _fmt_num


def _df():
    return pd.DataFrame({
        "src": ["a", "a", "b", "c", "a", "d"],
        "dst": ["b", "b", "a", "c", "c", "a"],
        "ts": pd.to_datetime(["2014-01-01"] * 6),
        "sign": [1, -1, -1, 1, -1, 1],
    })


def test_arestas_dirigidas_agrega_e_remove_loops():
    e = T.arestas_dirigidas(_df()).set_index(["src", "dst"])
    assert ("c", "c") not in e.index
    assert e.loc[("a", "b"), "count"] == 2 and e.loc[("a", "b"), "sign"] == 1   # soma 0 -> +1
    assert e.loc[("a", "c"), "sign"] == -1


def test_arestas_nao_dirigidas_junta_sentidos():
    e = T.arestas_nao_dirigidas(T.arestas_dirigidas(_df())).set_index(["src", "dst"])
    assert e.loc[("a", "b"), "count"] == 3          # a→b (2) + b→a (1)
    assert e.loc[("a", "b"), "sign"] == 1           # saldo ponderado: (+1)·2 + (−1)·1 = 1 > 0
    assert math.isclose(e.loc[("a", "b"), "w"], 1 / 3)


def test_robustez_r_e_metricas():
    assert R.r_remover(34671) == 1734
    adj = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}       # estrela
    m = R.metricas(R.remover(adj, {0}), n_original=4, fontes=10)
    assert m["B_c"] == 3 and math.isclose(m["D_isolados"], 1.0) and math.isclose(m["A_S"], 0.25)


def test_formatacao_brasileira():
    assert _fmt_num(35776) == "35.776"
    assert _fmt_num(0.1862) == "0,1862"
    assert _fmt_num(2464.5) == "2.464,5"
    tex = tabela_latex(pd.DataFrame({"x": [1.5]}, index=["a"]), "Legenda", "tab:x")
    assert "\\caption{Legenda}" in tex and "\\label{tab:x}" in tex and "1,5" in tex


def test_texto_brasileiro():
    from src.analise import br, pct
    assert br(35776) == "35.776" and br(0.01636) == "0,01636" and br(True) == "sim"
    assert br(25435.5313, 8) == "25.435,531" and pct(0.969) == "96,9%"


def test_escala_preserva_n_do_grafo():
    import networkx as nx
    from src import medicao as Me
    grafos = [nx.path_graph(50), nx.path_graph(200)]
    casos = {"BFS": (lambda G: {u: list(G[u]) for u in G}, lambda a, i: A.bfs(a, 0), lambda n, m: n + m)}
    df = Me.escala(casos, grafos, reps=3)
    assert df["n"].tolist() == [50, 200] and (df["reps"] == 3).all()


def test_macros_latex(tmp_path):
    import pytest
    from src.relatorio import escrever_macros
    p = escrever_macros({"diametro": 11, "caminhoMedio": 3.9136, "texto": "G13", "fracao": "96,9%"},
                        tmp_path / "v.tex")
    t = p.read_text(encoding="utf-8")
    assert "\\newcommand{\\diametro}{11}" in t and "{3{,}91}" in t and "{G13}" in t
    assert "{96{,}9\\%}" in t
    with pytest.raises(ValueError):
        escrever_macros({"com_sublinhado": 1}, tmp_path / "x.tex")
