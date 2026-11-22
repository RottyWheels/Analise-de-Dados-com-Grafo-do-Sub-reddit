"""Geradores próprios dos modelos clássicos (Erdős–Rényi está em metricas.erdos_renyi_gnm)."""
from __future__ import annotations

import random


def _adj_de_arestas(n: int, arestas) -> dict:
    adj = {i: [] for i in range(n)}
    for u, v in arestas:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def barabasi_albert(n: int, m: int, seed: int = 0) -> dict:
    """Ligação preferencial: cada novo vértice se liga a m vértices distintos, escolhidos com
    probabilidade proporcional ao grau (lista de vértices repetidos por grau)."""
    rng = random.Random(seed)
    arestas = []
    repetidos = []
    alvos = list(range(m))
    for novo in range(m, n):
        arestas.extend((novo, a) for a in alvos)
        repetidos.extend(alvos)
        repetidos.extend([novo] * m)
        escolhidos = set()
        while len(escolhidos) < m:
            escolhidos.add(rng.choice(repetidos))
        alvos = list(escolhidos)
    return _adj_de_arestas(n, arestas)


def watts_strogatz(n: int, k: int, p: float, seed: int = 0) -> dict:
    """Anel regular em que cada vértice se liga aos k/2 vizinhos de cada lado; cada aresta
    (u, u+j) é religada com probabilidade p para um destino uniforme, sem laços nem duplicatas."""
    rng = random.Random(seed)
    viz = {i: set() for i in range(n)}
    for u in range(n):
        for j in range(1, k // 2 + 1):
            v = (u + j) % n
            viz[u].add(v)
            viz[v].add(u)
    for j in range(1, k // 2 + 1):
        for u in range(n):
            v = (u + j) % n
            if rng.random() < p and v in viz[u]:
                w = rng.randrange(n)
                while w == u or w in viz[u]:
                    if len(viz[u]) >= n - 1:
                        break
                    w = rng.randrange(n)
                else:
                    viz[u].discard(v)
                    viz[v].discard(u)
                    viz[u].add(w)
                    viz[w].add(u)
    return {u: list(vs) for u, vs in viz.items()}
