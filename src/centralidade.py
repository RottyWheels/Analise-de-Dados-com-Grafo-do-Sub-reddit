"""Centralidades com implementação própria: betweenness (Brandes) e PageRank (iteração de potência)."""
from __future__ import annotations

import random
from collections import deque


def betweenness_brandes(adj: dict, fontes: int | None = None, seed: int = 0) -> dict:
    """Betweenness de vértices em grafo não dirigido e não ponderado (Brandes, 2001). O(k·(n + m)).

    fontes=None usa todos os vértices (exato). Com k fontes sorteadas, o acúmulo é multiplicado
    por n/k (estimador não viesado; Brandes & Pich, 2007). Escala: cada par não ordenado {s, t}
    conta uma vez, como no igraph e no networkx com normalized=False.
    """
    nos = list(adj)
    n = len(nos)
    if fontes is None or fontes >= n:
        amostra, escala = nos, 1.0
    else:
        amostra, escala = random.Random(seed).sample(nos, fontes), n / fontes
    cb = dict.fromkeys(nos, 0.0)
    for s in amostra:
        pilha = []
        pred = {s: []}
        sigma = {s: 1}
        dist = {s: 0}
        fila = deque([s])
        while fila:
            v = fila.popleft()
            pilha.append(v)
            dv = dist[v] + 1
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dv
                    fila.append(w)
                    sigma[w] = 0
                    pred[w] = []
                if dist[w] == dv:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = dict.fromkeys(pilha, 0.0)
        while pilha:
            w = pilha.pop()
            coef = (1.0 + delta[w]) / sigma[w]
            for v in pred[w]:
                delta[v] += sigma[v] * coef
            if w != s:
                cb[w] += delta[w]
    fator = escala / 2.0  # não dirigido: cada par aparece a partir das duas pontas
    return {v: c * fator for v, c in cb.items()}


def pagerank(succ: dict, pesos: dict | None = None, alfa: float = 0.85,
             tol: float = 1e-10, max_iter: int = 200) -> dict:
    """PageRank por iteração de potência em grafo dirigido.

    succ[u] = [v, ...]; pesos[(u, v)] = peso da aresta (padrão 1). Vértices sem saída
    (dangling) distribuem sua massa uniformemente. Converge quando a variação L1 < n·tol.
    """
    nos = list(succ)
    n = len(nos)
    saida = {}
    for u in nos:
        ws = [(v, pesos[(u, v)] if pesos else 1.0) for v in succ[u]]
        tot = sum(w for _, w in ws)
        saida[u] = [(v, w / tot) for v, w in ws] if tot else []
    pr = dict.fromkeys(nos, 1.0 / n)
    for _ in range(max_iter):
        massa_dang = alfa * sum(pr[u] for u in nos if not saida[u]) / n
        novo = dict.fromkeys(nos, (1.0 - alfa) / n + massa_dang)
        for u in nos:
            pu = alfa * pr[u]
            for v, w in saida[u]:
                novo[v] += pu * w
        erro = sum(abs(novo[u] - pr[u]) for u in nos)
        pr = novo
        if erro < n * tol:
            break
    return pr
