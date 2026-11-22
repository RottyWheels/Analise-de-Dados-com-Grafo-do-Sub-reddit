"""Métricas estruturais, small-world, lei de potência e medição de tempo (código próprio)."""
from __future__ import annotations

import math
import random
import statistics
import time
from collections import Counter

import numpy as np

from .algoritmos import bfs


# ---------------------------------------------------------------- graus
def resumo_graus(adj: dict) -> dict:
    g = [len(v) for v in adj.values()]
    n = len(adj)
    m = sum(g) // 2
    return {"n": n, "m": m, "grau_min": min(g), "grau_max": max(g),
            "grau_medio": sum(g) / n, "densidade": 2 * m / (n * (n - 1))}


def distribuicao_graus(adj: dict):
    """Retorna (k, P(k)) ordenados por k, só para k >= 1 com P(k) > 0
    (vértices isolados, k = 0, não entram no gráfico log-log)."""
    cont = Counter(len(v) for v in adj.values())
    cont.pop(0, None)
    n = len(adj)
    ks = np.array(sorted(cont))
    pk = np.array([cont[k] / n for k in ks])
    return ks, pk


def ccdf(adj: dict):
    """P(K >= k) para cada grau k observado."""
    ks, pk = distribuicao_graus(adj)
    return ks, pk[::-1].cumsum()[::-1]


# ---------------------------------------------------------------- triângulos / clusterização
def triangulos_por_vertice(adj: dict) -> dict:
    """Conta triângulos por vértice via interseção de vizinhanças com ordenação
    por grau (cada triângulo é encontrado uma única vez). O(m^{3/2})."""
    ordem = {u: (len(adj[u]), u) for u in adj}
    sup = {u: {v for v in adj[u] if ordem[v] > ordem[u]} for u in adj}
    t = dict.fromkeys(adj, 0)
    for u in adj:
        su = sup[u]
        for v in su:
            for w in su & sup[v]:
                t[u] += 1
                t[v] += 1
                t[w] += 1
    return t


def clusterizacao(adj: dict, tri: dict | None = None):
    """Retorna (C médio local, transitividade global, total de triângulos)."""
    tri = tri or triangulos_por_vertice(adj)
    soma_c = 0.0
    triplas = 0
    for u, vs in adj.items():
        k = len(vs)
        if k >= 2:
            pares = k * (k - 1) / 2
            soma_c += tri[u] / pares
            triplas += pares
    total = sum(tri.values()) // 3
    return soma_c / len(adj), 3 * total / triplas if triplas else 0.0, total


# ---------------------------------------------------------------- distâncias
def caminho_medio_amostrado(adj: dict, fontes: int = 1000, seed: int = 0):
    """Comprimento médio dos caminhos e excentricidades a partir de `fontes` BFS
    sorteadas (grafo conexo). Retorna (L estimado, maior distância vista, ecc das fontes)."""
    rng = random.Random(seed)
    nos = list(adj)
    amostra = nos if fontes >= len(nos) else rng.sample(nos, fontes)
    soma = cont = 0
    ecc = {}
    for s in amostra:
        d = bfs(adj, s)
        soma += sum(d.values())
        cont += len(d) - 1
        ecc[s] = max(d.values())
    return soma / cont, max(ecc.values()), ecc


# ---------------------------------------------------------------- grafos aleatórios
def erdos_renyi_gnm(n: int, m: int, seed: int = 0) -> dict:
    """G(n, m) próprio: sorteia m arestas distintas sem laços."""
    rng = random.Random(seed)
    arestas = set()
    while len(arestas) < m:
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            arestas.add((u, v) if u < v else (v, u))
    adj = {i: [] for i in range(n)}
    for u, v in arestas:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def maior_componente_adj(adj: dict) -> dict:
    from .algoritmos import componentes_conexas
    c = componentes_conexas(adj)[0]
    return {u: [v for v in adj[u] if v in c] for u in c}


def small_world(adj: dict, reps: int = 5, fontes: int = 300, seed: int = 0) -> dict:
    """Critério do enunciado: L(G) ≈ L_aleatório e C(G) ≫ C_aleatório.
    Aleatório = G(n, m) com mesmo n e m (mesmo grau médio)."""
    n = len(adj)
    m = sum(len(v) for v in adj.values()) // 2
    k = 2 * m / n
    C_G, _, _ = clusterizacao(adj)
    L_G, _, _ = caminho_medio_amostrado(adj, fontes, seed)
    Cs, Ls = [], []
    for r in range(reps):
        a = erdos_renyi_gnm(n, m, seed + r)
        Cs.append(clusterizacao(a)[0])
        Ls.append(caminho_medio_amostrado(maior_componente_adj(a), fontes, seed + r)[0])
    C_r, L_r = statistics.mean(Cs), statistics.mean(Ls)
    return {
        "n": n, "m": m, "grau_medio": k,
        "C(G)": C_G, "C_aleatorio": C_r, "C_aleatorio_teorico": k / n, "C(G)/C_aleatorio": C_G / C_r,
        "L(G)": L_G, "L_aleatorio": L_r, "L_aleatorio_teorico": math.log(n) / math.log(k),
        "L(G)/L_aleatorio": L_G / L_r,
        "sigma": (C_G / C_r) / (L_G / L_r),
    }


# ---------------------------------------------------------------- lei de potência
def regressao_loglog(x, y) -> dict:
    lx, ly = np.log10(x), np.log10(y)
    a, b = np.polyfit(lx, ly, 1)
    pred = a * lx + b
    r2 = 1 - ((ly - pred) ** 2).sum() / ((ly - ly.mean()) ** 2).sum()
    return {"inclinacao": a, "intercepto": b, "r2": r2}


def lei_potencia(adj: dict, kmin_mle: int | None = None) -> dict:
    """γ por regressão em log P(k) vs log k (método do enunciado; P(k) bruto e com bins
    logarítmicos), pela CCDF
    (inclinação = −(γ−1)) e por máxima verossimilhança discreta aproximada (Clauset)."""
    ks, pk = distribuicao_graus(adj)
    rp = regressao_loglog(ks, pk)
    # histograma com bins logarítmicos (densidade por largura de bin): reduz o ruído da cauda,
    # onde muitos graus aparecem uma única vez e "achatam" a regressão em P(k) bruto
    graus_pos = np.array([len(v) for v in adj.values() if v])
    bordas = np.unique(np.floor(np.logspace(0, np.log10(graus_pos.max() + 1), 30)).astype(int))
    hist, _ = np.histogram(graus_pos, bins=bordas)
    dens = hist / (np.diff(bordas) * len(graus_pos))
    centros = np.sqrt(bordas[:-1] * bordas[1:])
    ok = dens > 0
    rb = regressao_loglog(centros[ok], dens[ok])
    kc, pc = ccdf(adj)
    rc = regressao_loglog(kc, pc)
    graus = np.array([len(v) for v in adj.values()])
    graus = graus[graus > 0]
    mle = mle_clauset(graus, kmin_mle)
    return {"gamma_pk": -rp["inclinacao"], "r2_pk": rp["r2"], "logC_pk": rp["intercepto"],
            "gamma_pk_bins_log": -rb["inclinacao"], "r2_pk_bins_log": rb["r2"], "logC_pk_bins_log": rb["intercepto"],
            "gamma_ccdf": 1 - rc["inclinacao"], "r2_ccdf": rc["r2"],
            "gamma_mle": mle["gamma"], "kmin_mle": mle["kmin"], "ks_mle": mle["ks"],
            "n_cauda_mle": mle["n_cauda"]}


def mle_clauset(graus: np.ndarray, kmin: int | None = None) -> dict:
    """γ = 1 + n / Σ ln(k / (kmin − 0.5)); kmin escolhido minimizando a distância KS."""
    def ajuste(km):
        x = graus[graus >= km]
        g = 1 + len(x) / np.log(x / (km - 0.5)).sum()
        xs = np.sort(x)
        emp = np.arange(1, len(xs) + 1) / len(xs)
        teo = 1 - (xs / km) ** (1 - g)
        return g, np.abs(emp - teo).max(), len(x)

    candidatos = [kmin] if kmin else [k for k in np.unique(graus) if (graus >= k).sum() >= 50][:200]
    melhor = min(((km, *ajuste(km)) for km in candidatos), key=lambda t: t[2])
    return {"kmin": int(melhor[0]), "gamma": melhor[1], "ks": melhor[2], "n_cauda": melhor[3]}


# ---------------------------------------------------------------- tempo de execução
def intervalo_confianca(amostras, conf: float = 0.95) -> dict:
    """IC conforme o enunciado: n >= 30 -> Normal (z); n < 30 -> t-Student."""
    from scipy import stats
    n = len(amostras)
    media = statistics.mean(amostras)
    dp = statistics.stdev(amostras) if n > 1 else 0.0
    if n >= 30:
        crit, dist = stats.norm.ppf(1 - (1 - conf) / 2), "Normal (z)"
    else:
        crit, dist = stats.t.ppf(1 - (1 - conf) / 2, n - 1), "t-Student"
    h = crit * dp / math.sqrt(n)
    return {"n": n, "media_s": media, "desvio_s": dp, "ic_inf_s": media - h, "ic_sup_s": media + h,
            "distribuicao": dist}


def medir(func, entradas, reps: int = 30) -> dict:
    """Executa func(*entradas[i % len(entradas)]) `reps` vezes e devolve estatísticas."""
    tempos = []
    for i in range(reps):
        args = entradas[i % len(entradas)]
        t0 = time.perf_counter()
        func(*args)
        tempos.append(time.perf_counter() - t0)
    return intervalo_confianca(tempos)
