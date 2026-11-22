"""Robustez (Apêndice C): remoção aleatória e ataque direcionado de 5% dos vértices."""
from __future__ import annotations

import math
import random

from .algoritmos import componentes_conexas
from .metricas import caminho_medio_amostrado


def remover(adj: dict, removidos: set) -> dict:
    return {u: [v for v in vs if v not in removidos] for u, vs in adj.items() if u not in removidos}


def metricas(adj: dict, n_original: int, fontes: int = 200, seed: int = 0) -> dict:
    """A: tamanho relativo da maior componente (S); B: nº de componentes (c);
    C: comprimento médio dos caminhos na maior componente (amostrado);
    D: fração de vértices isolados."""
    comps = componentes_conexas(adj)
    gc = comps[0]
    sub = {u: [v for v in adj[u] if v in gc] for u in gc}
    L, _, _ = caminho_medio_amostrado(sub, fontes, seed)
    iso = sum(1 for vs in adj.values() if not vs)
    return {"A_S": len(gc) / n_original, "B_c": len(comps), "C_L": L, "D_isolados": iso / len(adj)}


def r_remover(n: int) -> int:
    return math.ceil(0.05 * n)


def remocao_aleatoria(adj: dict, reps: int = 30, seed: int = 0, fontes: int = 200) -> list:
    n = len(adj)
    r = r_remover(n)
    nos = list(adj)
    res = []
    for i in range(reps):
        rng = random.Random(seed + i)
        alvo = set(rng.sample(nos, r))
        res.append(metricas(remover(adj, alvo), n, fontes, seed + i))
    return res


def ataque_direcionado(adj: dict, centralidade: dict, fontes: int = 200, seed: int = 0) -> dict:
    """Ranking fixo: remove os r vértices de maior centralidade de uma só vez."""
    n = len(adj)
    r = r_remover(n)
    top = sorted(centralidade, key=centralidade.get, reverse=True)[:r]
    return metricas(remover(adj, set(top)), n, fontes, seed)
