import math

import networkx as nx
import numpy as np
import pytest

from src import algoritmos as A, metricas as M, medicao as Me, modelos as Mo


def test_triangulos_e_clusterizacao(G_pond):
    adj = A.lista_adj(G_pond)
    tri = M.triangulos_por_vertice(adj)
    assert tri == nx.triangles(G_pond)
    c, t, total = M.clusterizacao(adj, tri)
    assert math.isclose(c, nx.average_clustering(G_pond))
    assert math.isclose(t, nx.transitivity(G_pond))
    assert total == sum(tri.values()) // 3


def test_resumo_graus():
    G = nx.complete_graph(10)
    r = M.resumo_graus(A.lista_adj(G))
    assert r["n"] == 10 and r["m"] == 45 and r["densidade"] == 1.0 and r["grau_medio"] == 9


def test_caminho_medio_todas_as_fontes(G_pond):
    L, diam, _ = M.caminho_medio_amostrado(A.lista_adj(G_pond), fontes=10**6)
    assert math.isclose(L, nx.average_shortest_path_length(G_pond))
    assert diam == nx.diameter(G_pond)


def test_erdos_renyi_gnm():
    adj = M.erdos_renyi_gnm(500, 2000, seed=1)
    assert len(adj) == 500
    assert sum(map(len, adj.values())) == 4000
    assert all(u not in vs for u, vs in adj.items())


def test_small_world_watts_strogatz():
    G = nx.connected_watts_strogatz_graph(2000, 10, 0.05, seed=1)
    sw = M.small_world(A.lista_adj(G), reps=2, fontes=100)
    assert sw["C(G)/C_aleatorio"] > 10 and sw["L(G)/L_aleatorio"] < 2


def test_lei_potencia_em_barabasi_albert():
    pl = M.lei_potencia(Mo.barabasi_albert(20000, 3, seed=1))
    assert 2.4 < pl["gamma_mle"] < 3.4
    assert pl["gamma_pk_bins_log"] > 1


def test_isolados_fora_da_distribuicao():
    ks, pk = M.distribuicao_graus({0: [1], 1: [0], 2: []})
    assert ks.tolist() == [1]


@pytest.mark.parametrize("n, dist", [(30, "Normal (z)"), (10, "t-Student")])
def test_intervalo_confianca(n, dist):
    amostras = list(np.linspace(1, 2, n))
    ic = Me.intervalo_confianca(amostras)
    assert ic["distribuicao"] == dist
    assert ic["ic_inf_s"] < ic["media_s"] < ic["ic_sup_s"]
    if n >= 30:
        assert math.isclose(ic["valor_critico"], 1.959964, rel_tol=1e-5)


def test_ajuste_linear():
    x = np.array([1, 2, 4, 8.0])
    r = Me.ajustar(3 * x, x)
    assert math.isclose(r["c"], 3) and math.isclose(r["r2"], 1)


def test_modelos_geradores():
    ba = Mo.barabasi_albert(3000, 3, seed=2)
    assert sum(map(len, ba.values())) // 2 == 3 * (3000 - 3)
    ws = Mo.watts_strogatz(3000, 6, 0.2, seed=2)
    assert sum(map(len, ws.values())) // 2 == 3000 * 3
    assert all(u not in vs and len(vs) == len(set(vs)) for u, vs in ws.items())


def test_ajuste_n_m():
    n = np.array([100, 200, 400, 800.0])
    m = np.array([1700, 3200, 4800, 6400.0])
    r = Me.ajustar_n_m(2e-6 * n + 5e-7 * m, n, m)
    assert math.isclose(r["a_por_vertice"], 2e-6) and math.isclose(r["b_por_aresta"], 5e-7)
    assert math.isclose(r["r2"], 1)
