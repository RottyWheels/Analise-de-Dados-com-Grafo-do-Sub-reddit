"""Carga e tratamento do soc-redditHyperlinks-body.tsv (G13)."""
from __future__ import annotations

import random
from collections import deque
from pathlib import Path

import networkx as nx
import pandas as pd

COLUNAS = ["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "TIMESTAMP", "LINK_SENTIMENT"]


def carregar_bruto(caminho: str | Path) -> pd.DataFrame:
    """Lê o TSV mantendo só origem, destino, data e sinal (descarta PROPERTIES)."""
    df = pd.read_csv(caminho, sep="\t", usecols=COLUNAS)
    df.columns = ["src", "dst", "ts", "sign"]
    df["ts"] = pd.to_datetime(df["ts"])
    return df


def descrever_bruto(df: pd.DataFrame) -> dict:
    pares = df.groupby(["src", "dst"]).size()
    return {
        "posts (linhas)": len(df),
        "subreddits distintos": len(pd.unique(df[["src", "dst"]].values.ravel())),
        "pares dirigidos distintos": len(pares),
        "posts por par (média)": round(pares.mean(), 3),
        "posts por par (máximo)": int(pares.max()),
        "links positivos (+1)": int((df["sign"] == 1).sum()),
        "links negativos (-1)": int((df["sign"] == -1).sum()),
        "auto-loops": int((df["src"] == df["dst"]).sum()),
        "início": str(df["ts"].min()),
        "fim": str(df["ts"].max()),
    }


def arestas_dirigidas(df: pd.DataFrame) -> pd.DataFrame:
    """Temporal -> estático e multigrafo -> simples (dirigido).

    count = nº de posts do par; sign = sinal majoritário (+1 se soma >= 0).
    """
    df = df[df["src"] != df["dst"]]
    agg = df.groupby(["src", "dst"]).agg(count=("sign", "size"), soma=("sign", "sum")).reset_index()
    agg["sign"] = (agg["soma"] >= 0).map({True: 1, False: -1})
    return agg[["src", "dst", "count", "sign"]]


def arestas_nao_dirigidas(e_dir: pd.DataFrame) -> pd.DataFrame:
    """Dirigido -> não dirigido: junta (u,v) e (v,u), somando contagens e sinais."""
    a = e_dir.copy()
    troca = a["src"] > a["dst"]
    a.loc[troca, ["src", "dst"]] = a.loc[troca, ["dst", "src"]].values
    a["soma"] = a["sign"] * a["count"]
    agg = a.groupby(["src", "dst"]).agg(count=("count", "sum"), soma=("soma", "sum")).reset_index()
    agg["sign"] = (agg["soma"] >= 0).map({True: 1, False: -1})
    agg["w"] = 1.0 / agg["count"]
    return agg[["src", "dst", "count", "sign", "w"]]


def grafo_dirigido(e_dir: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_weighted_edges_from(zip(e_dir["src"], e_dir["dst"], 1.0 / e_dir["count"]))
    nx.set_edge_attributes(G, dict(zip(zip(e_dir["src"], e_dir["dst"]), e_dir["sign"])), "sign")
    nx.set_edge_attributes(G, dict(zip(zip(e_dir["src"], e_dir["dst"]), e_dir["count"])), "count")
    return G


def grafo_nao_dirigido(e_und: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    for u, v, c, s, w in e_und.itertuples(index=False):
        G.add_edge(u, v, count=int(c), sign=int(s), weight=float(w))
    return G


def maior_componente(G: nx.Graph) -> nx.Graph:
    nos = max(nx.connected_components(G), key=len)
    return G.subgraph(nos).copy()


def subgrafo_bfs(G: nx.Graph, n: int, raiz=None, seed: int = 0) -> nx.Graph:
    """Subgrafo induzido conexo com n vértices, coletados por BFS a partir de `raiz`
    (por padrão, um vértice sorteado). Usado para Floyd-Warshall e medições de tempo."""
    rng = random.Random(seed)
    if raiz is None:
        raiz = rng.choice(list(G.nodes))
    vistos = {raiz}
    fila = deque([raiz])
    while fila and len(vistos) < n:
        u = fila.popleft()
        viz = list(G.neighbors(u))
        rng.shuffle(viz)
        for v in viz:
            if v not in vistos:
                vistos.add(v)
                fila.append(v)
                if len(vistos) >= n:
                    break
    return G.subgraph(vistos).copy()
