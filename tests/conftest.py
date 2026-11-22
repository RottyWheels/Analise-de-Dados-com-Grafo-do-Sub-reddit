import random
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def G_pond():
    """Grafo não dirigido conexo com pesos positivos."""
    G = nx.connected_watts_strogatz_graph(300, 6, 0.3, seed=7)
    rng = random.Random(7)
    for u, v in G.edges:
        G[u][v]["weight"] = rng.uniform(0.1, 3.0)
    return G


@pytest.fixture(scope="session")
def G_desconexo():
    return nx.disjoint_union(nx.gnm_random_graph(150, 400, seed=1), nx.gnm_random_graph(60, 120, seed=2))


@pytest.fixture(scope="session")
def D_dir():
    return nx.gnm_random_graph(400, 1300, seed=3, directed=True)
