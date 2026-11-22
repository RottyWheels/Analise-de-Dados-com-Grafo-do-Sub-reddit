"""Montagem das tabelas e dos experimentos de cada seção do notebook."""
from __future__ import annotations

import math
import random

import pandas as pd

from . import algoritmos as A
from . import centralidade as Ce
from . import metricas as M
from . import modelos as Mo
from . import tratamento as T


# ---------------------------------------------------------------- formatação em português
def br(x, casas: int = 4) -> str:
    """Texto em formato brasileiro (para células de tabela): 35.776 · 0,1862 · 96,9% · sim/não."""
    if isinstance(x, bool):
        return "sim" if x else "não"
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer() and abs(x) >= 1000):
        return f"{int(x):,}".replace(",", ".")
    if abs(x) >= 1000:  # casas > 5 mantém decimais (ex.: br(25435.5313, 8) -> 25.435,531)
        return f"{x:,.{max(0, casas - 5)}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{x:.{casas}g}".replace(".", ",")


def pct(x: float, casas: int = 1) -> str:
    return f"{100 * x:.{casas}f}%".replace(".", ",")


# ---------------------------------------------------------------- matrícula
def indice_grafo(M_: int, verbose: bool = True) -> int:
    """f(M) = ((soma dos dígitos de M) × (últimos 2 dígitos de M + 1)) mod 129; 0 -> 129."""
    s = sum(int(d) for d in str(M_))
    u = M_ % 100
    r = (s * (u + 1)) % 129
    if verbose:
        print(f"soma dos dígitos = {s}; últimos 2 dígitos = {u:02d}")
        print(f"({s} × {u + 1}) mod 129 = {s * (u + 1)} mod 129 = {r}")
    return r or 129


# ---------------------------------------------------------------- tratamento
def tabela_tratamentos(df, e_dir, e_und, G_lcc) -> pd.DataFrame:
    return pd.DataFrame([
        ["Temporal → estático", "União de todos os posts de 31/12/2013 a 30/04/2017", f"{br(len(df))} posts"],
        ["Remoção de auto-loops", "Verificado: o arquivo não tem auto-loops", f"{int((df.src == df.dst).sum())} removidos"],
        ["Multigrafo → simples (dirigido)", "Uma aresta por par (u→v); count = nº de posts; sign = sinal majoritário", f"{br(len(e_dir))} arestas"],
        ["Dirigido → não dirigido", "Junta u→v e v→u; count somado; sign pelo saldo ponderado", f"{br(len(e_und))} arestas"],
        ["Pesos", "w = 1/count (pares com mais links ficam mais próximos)", "Dijkstra, Bellman-Ford, Floyd-Warshall, AGM"],
        ["Maior componente conexa", "Usada em distâncias, small-world e robustez",
         f"{br(G_lcc.number_of_nodes())} vértices / {br(G_lcc.number_of_edges())} arestas"],
        ["Subgrafos de teste", "Subgrafos induzidos conexos por BFS (n = 100 a 16.000)", "Floyd-Warshall e curvas de tempo"],
        ["Atributos descartados", "Vetor PROPERTIES (86 atributos de texto) e POST_ID", "economia de memória"],
    ], columns=["Tratamento", "Descrição", "Resultado"]).set_index("Tratamento")


# ---------------------------------------------------------------- Parte I
def tabela_parte1(rg, comps, dist, clust) -> pd.DataFrame:
    C_med, transit, n_tri = clust
    n = rg["n"]
    return pd.DataFrame([
        ["Número de vértices", rg["n"], "G_und", "sim"],
        ["Número de arestas", rg["m"], "G_und", "sim"],
        ["Grau mínimo", rg["grau_min"], "G_und", "sim"],
        ["Grau máximo", rg["grau_max"], "G_und", "sim"],
        ["Grau médio", round(rg["grau_medio"], 4), "G_und", "sim"],
        ["Distribuição de graus", "figura 03", "G_und", "sim"],
        ["Densidade", rg["densidade"], "G_und", "sim"],
        ["Número de componentes conexas", len(comps), "G_und", "sim"],
        ["Tamanho de cada componente", "tabela 03", "G_und", "sim"],
        ["Tamanho da maior componente", f"{br(len(comps[0]))} ({pct(len(comps[0]) / n)})", "G_und", "sim"],
        ["Diâmetro", dist["diametro"], "maior componente", "sim (exato, BFS própria)"],
        ["Raio", dist["raio"], "maior componente", "sim (exato, BFS própria)"],
        ["Comprimento médio dos caminhos", round(dist["caminho_medio"], 4), "maior componente", "sim (exato, BFS própria)"],
        ["Coeficiente de clusterização médio", round(C_med, 4), "G_und", "sim"],
        ["Transitividade (clusterização global)", round(transit, 4), "G_und", "sim (extra)"],
        ["Número de triângulos", n_tri, "G_und", "sim"],
        ["Visualização", "figura 03b (versão reduzida)", "top 150 por grau", "sim"],
    ], columns=["Medida", "Valor", "Grafo", "Calculado?"]).set_index("Medida")


# ---------------------------------------------------------------- Parte II: tempo
def casos_tempo(G_lcc, G_dir, adj, adj_lcc, succ, pred, subs_fw, fontes):
    """Lista (nome, complexidade, grafo, função, entradas) para medir com 30 repetições."""
    awL, eL, nosL = A.lista_adj_ponderada(G_lcc), A.lista_arestas(G_lcc), list(G_lcc)
    casos = [
        ("BFS", "O(n + m)", "maior componente", lambda s: A.bfs(adj_lcc, s), [(s,) for s in fontes]),
        ("DFS", "O(n + m)", "maior componente", lambda s: A.dfs(adj_lcc, s), [(s,) for s in fontes]),
        ("Euler (não dirigido)", "O(n + m)", "G_und", lambda: A.euleriano_nao_dirigido(adj), [()]),
        ("Euler (dirigido)", "O(n + m)", "G_dir", lambda: A.euleriano_dirigido(succ, pred), [()]),
        ("Dijkstra", "O((n + m) log n)", "maior componente", lambda s: A.dijkstra(awL, s), [(s,) for s in fontes]),
        ("Bellman-Ford", "O(n · m)", "maior componente",
         lambda s: A.bellman_ford(nosL, eL, s, dirigido=False), [(s,) for s in fontes]),
        ("Tarjan (SCC)", "O(n + m)", "G_dir", lambda: A.tarjan_scc(succ), [()]),
        ("Kruskal", "O(m log m)", "maior componente", lambda: A.kruskal(nosL, eL), [()]),
        ("Prim", "O(m log n)", "maior componente", lambda: A.prim(awL), [()]),
    ]
    casos += [(f"Floyd-Warshall (n={n})", "O(n³)", f"subgrafo n={n}", (lambda S: lambda: A.floyd_warshall(S))(S_), [()])
              for n, S_ in subs_fw.items()]
    return casos


def casos_escala(G_dir):
    """Casos para medicao.escala: (preparar, executar, f(n, m)). Tarjan usa o subgrafo dirigido
    induzido pelos mesmos vértices."""
    def fontes(G, k=30, seed=0):
        return random.Random(seed).sample(list(G), min(k, G.number_of_nodes()))

    def prep_adj(G):
        return A.lista_adj(G), fontes(G)

    def prep_w(G):
        return A.lista_adj_ponderada(G), A.lista_arestas(G), list(G), fontes(G)

    def prep_dir(G):
        D = G_dir.subgraph(G.nodes)
        return ({u: list(D.successors(u)) for u in D}, {u: list(D.predecessors(u)) for u in D})

    lg = lambda x: math.log2(max(x, 2))
    return {
        "BFS": (prep_adj, lambda e, i: A.bfs(e[0], e[1][i % len(e[1])]), lambda n, m: n + m),
        "DFS": (prep_adj, lambda e, i: A.dfs(e[0], e[1][i % len(e[1])]), lambda n, m: n + m),
        "Euler (não dirigido)": (prep_adj, lambda e, i: A.euleriano_nao_dirigido(e[0]), lambda n, m: n + m),
        "Euler (dirigido)": (prep_dir, lambda e, i: A.euleriano_dirigido(*e), lambda n, m: n + m),
        "Tarjan (SCC)": (prep_dir, lambda e, i: A.tarjan_scc(e[0]), lambda n, m: n + m),
        "Dijkstra": (prep_w, lambda e, i: A.dijkstra(e[0], e[3][i % len(e[3])]), lambda n, m: (n + m) * lg(n)),
        "Bellman-Ford": (prep_w, lambda e, i: A.bellman_ford(e[2], e[1], e[3][i % len(e[3])], dirigido=False),
                         lambda n, m: n * m),
        "Kruskal": (prep_w, lambda e, i: A.kruskal(e[2], e[1]), lambda n, m: m * lg(m)),
        "Prim": (prep_w, lambda e, i: A.prim(e[0]), lambda n, m: m * lg(n)),
    }


# ---------------------------------------------------------------- Parte III: descobertas
def top10(d: dict) -> list:
    return [f"{k} ({br(v)})" for k, v in sorted(d.items(), key=lambda x: -x[1])[:10]]


def tabela_hubs(G_dir, btw: dict, pr: dict) -> pd.DataFrame:
    return pd.DataFrame({"grau de entrada": top10(dict(G_dir.in_degree)),
                         "grau de saída": top10(dict(G_dir.out_degree)),
                         "PageRank": top10(pr), "betweenness (Brandes)": top10(btw)}, index=range(1, 11))


def tabela_negativos(df) -> pd.DataFrame:
    neg = df[df.sign == -1]
    return pd.DataFrame({
        "mais links negativos enviados": [f"{k} ({v})" for k, v in neg.src.value_counts().head(10).items()],
        "mais links negativos recebidos": [f"{k} ({v})" for k, v in neg.dst.value_counts().head(10).items()],
    }, index=range(1, 11))


# ---------------------------------------------------------------- extra: modelos
def gerar_modelos(adj_lcc: dict, seed: int = 1) -> dict:
    n = len(adj_lcc)
    m = sum(map(len, adj_lcc.values())) // 2
    k = max(1, round(m / n))  # BA com k arestas por vértice novo ≈ mesmo m
    return {
        "G13 (maior componente)": adj_lcc,
        "Erdős–Rényi G(n,m)": M.erdos_renyi_gnm(n, m, seed),
        f"Barabási–Albert (m={k})": Mo.barabasi_albert(n, k, seed),
        f"Watts–Strogatz (k={2 * k}, p=0,1)": Mo.watts_strogatz(n, 2 * k, 0.1, seed),
    }


def tabela_modelos(modelos: dict, fontes: int = 200) -> pd.DataFrame:
    lin = []
    for nome, a in modelos.items():
        amc = M.maior_componente_adj(a)
        c_, _, _ = M.clusterizacao(a)
        L_, _, _ = M.caminho_medio_amostrado(amc, fontes, 1)
        pl_ = M.lei_potencia(a)
        lin.append({"modelo": nome, "n": len(a), "m": sum(map(len, a.values())) // 2,
                    "grau máx": max(map(len, a.values())), "C médio": c_, "L": L_,
                    "γ (bins log)": pl_["gamma_pk_bins_log"], "R² (bins log)": pl_["r2_pk_bins_log"],
                    "γ (MLE)": pl_["gamma_mle"]})
    return pd.DataFrame(lin).set_index("modelo")
