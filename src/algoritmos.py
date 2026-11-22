"""Implementações próprias dos algoritmos da disciplina.

Representação: listas de adjacência em dicionários.
  adj[u]  = [v, ...]                (não ponderado)
  adjw[u] = [(v, peso), ...]        (ponderado)
O networkx é usado só para construir o grafo e, no notebook, para validar resultados.
"""
from __future__ import annotations

import heapq
import math
from collections import deque

import numpy as np


# ---------------------------------------------------------------- conversões
def lista_adj(G) -> dict:
    return {u: list(G.neighbors(u)) for u in G.nodes}


def lista_adj_ponderada(G, peso: str = "weight") -> dict:
    return {u: [(v, d.get(peso, 1.0)) for v, d in G[u].items()] for u in G.nodes}


def lista_arestas(G, peso: str = "weight") -> list:
    return [(u, v, d.get(peso, 1.0)) for u, v, d in G.edges(data=True)]


# ---------------------------------------------------------------- buscas
def bfs(adj: dict, s) -> dict:
    """Busca em largura. Retorna {vértice: distância em saltos}. O(n + m)."""
    dist = {s: 0}
    fila = deque([s])
    while fila:
        u = fila.popleft()
        du = dist[u] + 1
        for v in adj[u]:
            if v not in dist:
                dist[v] = du
                fila.append(v)
    return dist


def dfs(adj: dict, s) -> list:
    """Busca em profundidade iterativa (pilha explícita). Retorna a ordem de visita. O(n + m)."""
    visit = {s}
    ordem = [s]
    pilha = [(s, iter(adj[s]))]
    while pilha:
        u, it = pilha[-1]
        for v in it:
            if v not in visit:
                visit.add(v)
                ordem.append(v)
                pilha.append((v, iter(adj[v])))
                break
        else:
            pilha.pop()
    return ordem


def componentes_conexas(adj: dict) -> list:
    """Componentes conexas via BFS repetida. Retorna lista de conjuntos (maior primeiro)."""
    vistos = set()
    comps = []
    for s in adj:
        if s not in vistos:
            c = set(bfs(adj, s))
            vistos |= c
            comps.append(c)
    return sorted(comps, key=len, reverse=True)


# ---------------------------------------------------------------- Euler
def euleriano_nao_dirigido(adj: dict) -> dict:
    """Euleriano (ciclo) sse conexo (ignorando isolados) e todos os graus pares.
    Semi-euleriano (caminho) sse conexo e exatamente 0 ou 2 vértices de grau ímpar."""
    impares = sum(1 for u in adj if len(adj[u]) % 2)
    nao_isolados = {u: vs for u, vs in adj.items() if vs}
    conexo = len(componentes_conexas(nao_isolados)) == 1 if nao_isolados else True
    return {
        "conexo": conexo,
        "vertices_grau_impar": impares,
        "euleriano": conexo and impares == 0,
        "semi_euleriano": conexo and impares in (0, 2),
    }


def euleriano_dirigido(succ: dict, pred: dict) -> dict:
    """Euleriano dirigido sse grau de entrada == grau de saída em todo vértice
    e o grafo é fracamente conexo (ignorando isolados)."""
    desbal = sum(1 for u in succ if len(succ[u]) != len(pred[u]))
    und = {u: list(set(succ[u]) | set(pred[u])) for u in succ}
    und = {u: vs for u, vs in und.items() if vs}
    conexo = len(componentes_conexas(und)) == 1
    return {"fracamente_conexo": conexo, "vertices_desbalanceados": desbal,
            "euleriano": conexo and desbal == 0}


# ---------------------------------------------------------------- caminhos mínimos
def dijkstra(adjw: dict, s) -> dict:
    """Dijkstra com heap binário. Pesos não negativos. O((n + m) log n)."""
    dist = {s: 0.0}
    heap = [(0.0, s)]
    fechado = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in fechado:
            continue
        fechado.add(u)
        for v, w in adjw[u]:
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def bellman_ford(nos, arestas: list, s, dirigido: bool = True):
    """Bellman-Ford com parada antecipada. Aceita pesos negativos. O(n·m).

    arestas: [(u, v, w)]. Se dirigido=False, cada aresta vale nos dois sentidos.
    Retorna (dist, tem_ciclo_negativo, iteracoes).
    """
    if not dirigido:
        arestas = arestas + [(v, u, w) for u, v, w in arestas]
    dist = {u: math.inf for u in nos}
    dist[s] = 0.0
    n = len(dist)
    it = 0
    for it in range(1, n):
        mudou = False
        for u, v, w in arestas:
            du = dist[u]
            if du + w < dist[v]:
                dist[v] = du + w
                mudou = True
        if not mudou:
            return dist, False, it
    ciclo_neg = any(dist[u] + w < dist[v] for u, v, w in arestas)
    return dist, ciclo_neg, it


def floyd_warshall(G, peso: str = "weight"):
    """Floyd-Warshall O(n³). Laço em k explícito; o passo de relaxamento de cada k
    é vetorizado com numpy (a mesma recorrência D[i,j] = min(D[i,j], D[i,k]+D[k,j]))."""
    nos = list(G.nodes)
    idx = {u: i for i, u in enumerate(nos)}
    n = len(nos)
    D = np.full((n, n), np.inf)
    np.fill_diagonal(D, 0.0)
    for u, v, d in G.edges(data=True):
        w = d.get(peso, 1.0)
        i, j = idx[u], idx[v]
        D[i, j] = min(D[i, j], w)
        if not G.is_directed():
            D[j, i] = min(D[j, i], w)
    for k in range(n):
        np.minimum(D, D[:, k, None] + D[None, k, :], out=D)
    return nos, D


# ---------------------------------------------------------------- Tarjan
def tarjan_scc(succ: dict) -> list:
    """Componentes fortemente conexas (Tarjan), versão iterativa. O(n + m)."""
    indice = {}
    low = {}
    na_pilha = set()
    pilha = []
    comps = []
    contador = 0
    for raiz in succ:
        if raiz in indice:
            continue
        trabalho = [(raiz, iter(succ[raiz]))]
        indice[raiz] = low[raiz] = contador
        contador += 1
        pilha.append(raiz)
        na_pilha.add(raiz)
        while trabalho:
            u, it = trabalho[-1]
            avancou = False
            for v in it:
                if v not in indice:
                    indice[v] = low[v] = contador
                    contador += 1
                    pilha.append(v)
                    na_pilha.add(v)
                    trabalho.append((v, iter(succ[v])))
                    avancou = True
                    break
                elif v in na_pilha:
                    low[u] = min(low[u], indice[v])
            if avancou:
                continue
            trabalho.pop()
            if trabalho:
                p = trabalho[-1][0]
                low[p] = min(low[p], low[u])
            if low[u] == indice[u]:
                comp = set()
                while True:
                    x = pilha.pop()
                    na_pilha.discard(x)
                    comp.add(x)
                    if x == u:
                        break
                comps.append(comp)
    return sorted(comps, key=len, reverse=True)


# ---------------------------------------------------------------- AGM
class UnionFind:
    def __init__(self, elems):
        self.pai = {e: e for e in elems}
        self.rank = {e: 0 for e in elems}

    def find(self, x):
        raiz = x
        while self.pai[raiz] != raiz:
            raiz = self.pai[raiz]
        while self.pai[x] != raiz:
            self.pai[x], x = raiz, self.pai[x]
        return raiz

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.pai[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(nos, arestas: list):
    """Kruskal com union-find. O(m log m). Retorna (arestas da AGM, peso total)."""
    uf = UnionFind(nos)
    agm, total = [], 0.0
    for u, v, w in sorted(arestas, key=lambda e: e[2]):
        if uf.union(u, v):
            agm.append((u, v, w))
            total += w
    return agm, total


def prim(adjw: dict):
    """Prim com heap binário (floresta geradora se desconexo). O(m log n)."""
    visit = set()
    agm, total = [], 0.0
    for raiz in adjw:
        if raiz in visit:
            continue
        visit.add(raiz)
        heap = [(w, raiz, v) for v, w in adjw[raiz]]
        heapq.heapify(heap)
        while heap:
            w, u, v = heapq.heappop(heap)
            if v in visit:
                continue
            visit.add(v)
            agm.append((u, v, w))
            total += w
            for x, wx in adjw[v]:
                if x not in visit:
                    heapq.heappush(heap, (wx, v, x))
    return agm, total


# ---------------------------------------------------------------- pontes e articulações (Tarjan)
def pontes_articulacoes(adj: dict):
    """Pontes e vértices de articulação de um grafo não dirigido (Tarjan, 1974), versão iterativa.

    Usa tempos de descoberta (disc) e o menor tempo alcançável pela subárvore (low):
    (u, v) é ponte se low[v] > disc[u]; u é articulação se é raiz com 2+ filhos na árvore
    de DFS, ou não raiz com algum filho v tal que low[v] >= disc[u]. O(n + m).
    """
    disc, low = {}, {}
    pontes, artic = [], set()
    t = 0
    for raiz in adj:
        if raiz in disc:
            continue
        disc[raiz] = low[raiz] = t
        t += 1
        filhos_raiz = 0
        pilha = [(raiz, None, iter(adj[raiz]))]
        while pilha:
            u, pai, it = pilha[-1]
            avancou = False
            for v in it:
                if v == pai:
                    continue
                if v not in disc:
                    disc[v] = low[v] = t
                    t += 1
                    if u == raiz:
                        filhos_raiz += 1
                    pilha.append((v, u, iter(adj[v])))
                    avancou = True
                    break
                low[u] = min(low[u], disc[v])
            if avancou:
                continue
            pilha.pop()
            if pai is not None:
                low[pai] = min(low[pai], low[u])
                if low[u] > disc[pai]:
                    pontes.append((pai, u))
                if pai != raiz and low[u] >= disc[pai]:
                    artic.add(pai)
        if filhos_raiz >= 2:
            artic.add(raiz)
    return pontes, artic


def floyd_warshall_puro(G, peso: str = "weight"):
    """Floyd-Warshall em Python puro (listas), com poda: para cada k, só percorre as linhas i
    que alcançam k. Mesmo resultado da versão numpy; serve para comparar as duas."""
    nos = list(G.nodes)
    idx = {u: i for i, u in enumerate(nos)}
    n = len(nos)
    inf = math.inf
    D = [[inf] * n for _ in range(n)]
    for i in range(n):
        D[i][i] = 0.0
    for u, v, d in G.edges(data=True):
        w = d.get(peso, 1.0)
        i, j = idx[u], idx[v]
        D[i][j] = min(D[i][j], w)
        if not G.is_directed():
            D[j][i] = min(D[j][i], w)
    for k in range(n):
        Dk = D[k]
        for i in range(n):
            Di = D[i]
            dik = Di[k]
            if dik == inf:
                continue
            for j in range(n):
                nd = dik + Dk[j]
                if nd < Di[j]:
                    Di[j] = nd
    return nos, D
