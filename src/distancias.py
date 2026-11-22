"""Distâncias exatas (diâmetro, raio, caminho médio) por BFS própria a partir de todos os vértices.

Para acelerar, o grafo é reindexado com inteiros (listas em vez de dicionários) e as BFS
podem ser distribuídas entre processos. O custo total é O(n·(n + m)).
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

_ADJ: list | None = None  # adjacência indexada, compartilhada com os processos


def indexar(adj: dict):
    """Converte {vértice: [vizinhos]} em (lista de nós, lista de listas de índices)."""
    nos = list(adj)
    idx = {u: i for i, u in enumerate(nos)}
    return nos, [[idx[v] for v in adj[u]] for u in nos]


def _bfs_int(s: int, adj: list) -> tuple[int, int, int]:
    """BFS sobre índices. Retorna (excentricidade, soma das distâncias, nº alcançados)."""
    n = len(adj)
    dist = [-1] * n
    dist[s] = 0
    fronteira = [s]
    d = soma = alc = 0
    while fronteira:
        d += 1
        prox = []
        for u in fronteira:
            for v in adj[u]:
                if dist[v] < 0:
                    dist[v] = d
                    prox.append(v)
        if prox:
            soma += d * len(prox)
            alc += len(prox)
            fronteira = prox
        else:
            break
    return d - 1, soma, alc


def _init(adj):
    global _ADJ
    _ADJ = adj


def _lote(fontes):
    return [(s, *_bfs_int(s, _ADJ)) for s in fontes]


def distancias_exatas(adj: dict, processos: int | None = None) -> dict:
    """BFS de todos os vértices de um grafo conexo.

    Retorna diâmetro, raio, comprimento médio dos caminhos e a excentricidade de cada vértice.
    processos=1 roda sem paralelismo; None usa todos os núcleos.
    """
    nos, a = indexar(adj)
    n = len(a)
    processos = processos or os.cpu_count() or 1
    if processos == 1:
        res = [(s, *_bfs_int(s, a)) for s in range(n)]
    else:
        tam = max(1, n // (processos * 20))
        lotes = [range(i, min(i + tam, n)) for i in range(0, n, tam)]
        with ProcessPoolExecutor(processos, initializer=_init, initargs=(a,)) as ex:
            res = [r for parte in ex.map(_lote, lotes) for r in parte]
    ecc = {nos[s]: e for s, e, _, _ in res}
    soma = sum(r[2] for r in res)
    pares = sum(r[3] for r in res)
    if pares != n * (n - 1):
        raise ValueError("grafo desconexo: use a maior componente")
    return {"diametro": max(ecc.values()), "raio": min(ecc.values()),
            "caminho_medio": soma / pares, "excentricidade": ecc}
