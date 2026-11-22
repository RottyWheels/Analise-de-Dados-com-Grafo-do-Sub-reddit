"""Medição de tempo de execução: IC conforme o enunciado e curvas de escala.

Para reduzir ruído: uma execução de aquecimento (descartada) antes das repetições e o
coletor de lixo do Python desligado durante cada cronometragem (gc.collect() entre elas).
"""
from __future__ import annotations

import gc
import math
import statistics
import time

import numpy as np


def intervalo_confianca(amostras, conf: float = 0.95) -> dict:
    """IC da média: n >= 30 -> Normal, x̄ ± z_{α/2}·s/√n; n < 30 -> t-Student, x̄ ± t_{α/2}·s/√n."""
    from scipy import stats
    n = len(amostras)
    media = statistics.mean(amostras)
    dp = statistics.stdev(amostras) if n > 1 else 0.0
    if n >= 30:
        crit, dist = stats.norm.ppf(1 - (1 - conf) / 2), "Normal (z)"
    else:
        crit, dist = stats.t.ppf(1 - (1 - conf) / 2, n - 1), "t-Student"
    h = crit * dp / math.sqrt(n)
    return {"n": n, "media_s": media, "desvio_s": dp, "ic_inf_s": media - h,
            "ic_sup_s": media + h, "valor_critico": crit, "distribuicao": dist}


def cronometrar(func, args=()) -> float:
    gc.collect()
    ativo = gc.isenabled()
    gc.disable()
    try:
        t0 = time.perf_counter()
        func(*args)
        return time.perf_counter() - t0
    finally:
        if ativo:
            gc.enable()


def medir(func, entradas, reps: int = 30, aquecimento: int = 1) -> dict:
    """Executa func(*entradas[i % len(entradas)]) `reps` vezes (após `aquecimento` execuções
    descartadas) e devolve média, desvio e IC."""
    for i in range(aquecimento):
        func(*entradas[i % len(entradas)])
    tempos = [cronometrar(func, entradas[i % len(entradas)]) for i in range(reps)]
    return intervalo_confianca(tempos)


def ajustar(t, x) -> dict:
    """Ajuste t ≈ c·x por mínimos quadrados (sem intercepto) e R² do ajuste."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    c = float(t @ x / (x @ x))
    res = t - c * x
    r2 = 1 - float(res @ res) / float(((t - t.mean()) ** 2).sum())
    return {"c": c, "r2": r2}


def escala(casos: dict, grafos: list, reps: int = 10) -> "pd.DataFrame":
    """Mede cada algoritmo em grafos de tamanho crescente.

    casos[nome] = (preparar, executar, f) onde
      preparar(G) -> estado (estruturas montadas fora da cronometragem),
      executar(estado, i) -> roda o algoritmo (i = índice da repetição, p/ variar a origem),
      f(n, m) -> custo teórico.
    Com reps < 30 o IC de cada tamanho usa t-Student, como pede o enunciado.
    """
    import pandas as pd
    linhas = []
    for G in grafos:
        n, m = G.number_of_nodes(), G.number_of_edges()
        for nome, (preparar, executar, f) in casos.items():
            est = preparar(G)
            ic = medir(lambda i: executar(est, i), [(i,) for i in range(reps)], reps=reps)
            linhas.append({"algoritmo": nome, "n": n, "m": m, "f(n,m)": f(n, m), **ic})
    df = pd.DataFrame(linhas)
    ajustes = {nome: ajustar(d["media_s"], d["f(n,m)"]) for nome, d in df.groupby("algoritmo")}
    df["c"] = df["algoritmo"].map(lambda a: ajustes[a]["c"])
    df["r2_ajuste"] = df["algoritmo"].map(lambda a: ajustes[a]["r2"])
    df["previsto_s"] = df["c"] * df["f(n,m)"]
    return df
