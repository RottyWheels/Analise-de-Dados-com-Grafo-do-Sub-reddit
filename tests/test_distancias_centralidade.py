import math

import networkx as nx
import pytest

from src import algoritmos as A, centralidade as Ce, distancias as D


@pytest.mark.parametrize("processos", [1, 2])
def test_distancias_exatas(G_pond, processos):
    r = D.distancias_exatas(A.lista_adj(G_pond), processos=processos)
    assert r["diametro"] == nx.diameter(G_pond)
    assert r["raio"] == nx.radius(G_pond)
    assert math.isclose(r["caminho_medio"], nx.average_shortest_path_length(G_pond))
    assert r["excentricidade"] == nx.eccentricity(G_pond)


def test_distancias_rejeita_desconexo(G_desconexo):
    with pytest.raises(ValueError):
        D.distancias_exatas(A.lista_adj(G_desconexo), processos=1)


def test_brandes_exato(G_pond):
    b = Ce.betweenness_brandes(A.lista_adj(G_pond))
    ref = nx.betweenness_centrality(G_pond, normalized=False)
    assert all(math.isclose(b[k], ref[k], abs_tol=1e-6) for k in ref)


def test_brandes_amostrado_aproxima(G_pond):
    """Com metade das fontes, o estimador escalado por n/k fica próximo do exato."""
    import numpy as np
    ref = nx.betweenness_centrality(G_pond, normalized=False)
    b = Ce.betweenness_brandes(A.lista_adj(G_pond), fontes=150, seed=1)
    x = np.array([ref[k] for k in ref])
    y = np.array([b[k] for k in ref])
    assert np.corrcoef(x, y)[0, 1] > 0.9
    assert math.isclose(y.sum(), x.sum(), rel_tol=0.1)


def test_pagerank_igual_networkx(D_dir):
    for u, v in D_dir.edges:
        D_dir[u][v]["w"] = 1 + (u * v) % 5
    succ = {u: list(D_dir.successors(u)) for u in D_dir}
    pesos = {(u, v): d["w"] for u, v, d in D_dir.edges(data=True)}
    pr = Ce.pagerank(succ, pesos)
    ref = nx.pagerank(D_dir, weight="w", tol=1e-12)
    assert math.isclose(sum(pr.values()), 1.0)
    assert all(math.isclose(pr[k], ref[k], abs_tol=1e-8) for k in ref)
