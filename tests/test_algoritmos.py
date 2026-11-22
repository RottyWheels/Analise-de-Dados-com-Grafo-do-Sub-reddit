import math

import networkx as nx
import pytest

from src import algoritmos as A


def test_bfs_igual_networkx(G_pond):
    adj = A.lista_adj(G_pond)
    for s in list(G_pond)[:20]:
        assert A.bfs(adj, s) == nx.single_source_shortest_path_length(G_pond, s)


def test_dfs_visita_componente_e_ordem_valida(G_desconexo):
    adj = A.lista_adj(G_desconexo)
    ordem = A.dfs(adj, 0)
    assert set(ordem) == nx.node_connected_component(G_desconexo, 0)
    assert len(ordem) == len(set(ordem))
    # cada vértice (exceto o primeiro) é vizinho de algum vértice visitado antes
    vistos = {ordem[0]}
    for v in ordem[1:]:
        assert any(u in vistos for u in adj[v])
        vistos.add(v)


def test_componentes_conexas(G_desconexo):
    comps = A.componentes_conexas(A.lista_adj(G_desconexo))
    ref = sorted(nx.connected_components(G_desconexo), key=len, reverse=True)
    assert [len(c) for c in comps] == [len(c) for c in ref]


@pytest.mark.parametrize("G, esperado", [
    (nx.cycle_graph(8), (True, True)),
    (nx.path_graph(6), (False, True)),
    (nx.star_graph(3), (False, False)),
])
def test_euler_nao_dirigido(G, esperado):
    r = A.euleriano_nao_dirigido(A.lista_adj(G))
    assert (r["euleriano"], r["semi_euleriano"]) == esperado
    assert r["euleriano"] == nx.is_eulerian(G)


def test_euler_dirigido():
    C = nx.cycle_graph(6, create_using=nx.DiGraph)
    P = nx.path_graph(6, create_using=nx.DiGraph)
    for G in (C, P):
        succ = {u: list(G.successors(u)) for u in G}
        pred = {u: list(G.predecessors(u)) for u in G}
        assert A.euleriano_dirigido(succ, pred)["euleriano"] == nx.is_eulerian(G)


def test_dijkstra_igual_networkx(G_pond):
    adjw = A.lista_adj_ponderada(G_pond)
    ref = nx.single_source_dijkstra_path_length(G_pond, 0)
    d = A.dijkstra(adjw, 0)
    assert d.keys() == ref.keys()
    assert all(math.isclose(d[k], ref[k]) for k in ref)


def test_bellman_ford_igual_dijkstra(G_pond):
    ref = nx.single_source_dijkstra_path_length(G_pond, 0)
    d, neg, it = A.bellman_ford(list(G_pond), A.lista_arestas(G_pond), 0, dirigido=False)
    assert not neg and it < len(G_pond)
    assert all(math.isclose(d[k], ref[k]) for k in ref)


def test_bellman_ford_detecta_ciclo_negativo():
    arestas = [(0, 1, 1.0), (1, 2, -2.0), (2, 0, 0.5), (2, 3, 1.0)]
    _, neg, _ = A.bellman_ford([0, 1, 2, 3], arestas, 0, dirigido=True)
    assert neg


def test_floyd_warshall_igual_networkx(G_pond):
    S = G_pond.subgraph(range(120)).copy()
    nos, D = A.floyd_warshall(S)
    ref = dict(nx.all_pairs_dijkstra_path_length(S))
    for i, u in enumerate(nos[:30]):
        for j, v in enumerate(nos):
            esperado = ref[u].get(v, math.inf)
            assert (math.isinf(D[i, j]) and math.isinf(esperado)) or math.isclose(D[i, j], esperado)


def test_tarjan_igual_networkx(D_dir):
    succ = {u: list(D_dir.successors(u)) for u in D_dir}
    scc = A.tarjan_scc(succ)
    ref = list(nx.strongly_connected_components(D_dir))
    assert sorted(map(frozenset, scc), key=sorted) == sorted(map(frozenset, ref), key=sorted)


def test_agm_kruskal_prim(G_pond):
    ref = sum(d["weight"] for *_, d in nx.minimum_spanning_edges(G_pond, data=True))
    agm_k, pk = A.kruskal(list(G_pond), A.lista_arestas(G_pond))
    agm_p, pp = A.prim(A.lista_adj_ponderada(G_pond))
    assert len(agm_k) == len(agm_p) == len(G_pond) - 1
    assert math.isclose(pk, ref) and math.isclose(pp, ref)


def test_prim_floresta_em_grafo_desconexo(G_desconexo):
    for u, v in G_desconexo.edges:
        G_desconexo[u][v]["weight"] = 1.0
    agm, _ = A.prim(A.lista_adj_ponderada(G_desconexo))
    assert len(agm) == len(G_desconexo) - nx.number_connected_components(G_desconexo)
