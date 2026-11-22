# Análise de Dados com o Grafo de Hiperlinks entre Subreddits

Trabalho prático **"Analisando Grafos do SNAP"** – Teoria dos Grafos, IC/UFBA (Prof. Bruno Pereira dos Santos).
Matrícula **224216276** → grafo **G13 – `soc-RedditHyperlinks`** (Social networks).

- Dataset: <https://snap.stanford.edu/data/soc-RedditHyperlinks.html> (Kumar, Hamilton, Leskovec & Jurafsky, *Community Interaction and Conflict on the Web*, WWW 2018)
- Arquivo usado: `soc-redditHyperlinks-body.tsv` (hiperlinks no corpo dos posts)
- Checklist do trabalho: [`CHECKLIST.md`](CHECKLIST.md)

## Estrutura

```
.
├── notebook.ipynb            # análise completa (Partes I, II, III e extra), já executado
├── src/
│   ├── tratamento.py         # carga do TSV e tratamento (temporal→estático, multigrafo→simples, ...)
│   ├── algoritmos.py         # BFS, DFS, Euler, Dijkstra, Bellman-Ford, Floyd-Warshall, Tarjan, Kruskal, Prim
│   ├── metricas.py           # graus, triângulos, clusterização, caminhos, small-world, lei de potência, IC
│   └── robustez.py           # remoção aleatória e ataque direcionado (Apêndice C)
├── data/
│   ├── raw/download.py       # baixa o TSV original (319 MB, não versionado)
│   └── processed/            # arestas tratadas (versionadas)
├── figuras/                  # figuras usadas no relatório (PNG)
├── resultados/               # tabelas em CSV e LaTeX (.tex) para o Overleaf
└── requirements.txt
```

## Como executar

Requer Python 3.10+.

```bash
# 1. ambiente
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. dados brutos (~319 MB)
python data/raw/download.py

# 3. análise
jupyter notebook notebook.ipynb    # Kernel → Restart & Run All
```

A execução completa leva cerca de 20–30 minutos (as etapas mais demoradas são distâncias exatas,
betweenness e as 30 repetições de robustez). O notebook já está salvo com as saídas.

## Tratamento dos dados (resumo)

| Passo | Decisão |
|---|---|
| Temporal → estático | união de todos os posts (31/12/2013 a 30/04/2017) |
| Auto-loops | verificados (0 no arquivo) |
| Multigrafo → simples | uma aresta por par; `count` = nº de posts, `sign` = sinal majoritário |
| Dirigido → não dirigido | junta u→v e v→u (dirigido mantido para Tarjan e Euler dirigido) |
| Pesos | `w = 1/count` (Dijkstra, Bellman-Ford, Floyd-Warshall, AGM) |
| Maior componente conexa | usada em distâncias, small-world e robustez |
| Subgrafos por BFS | Floyd-Warshall (O(n³)) e curvas de tempo |

Arquivos em `data/processed/`:

- `arestas_dirigidas.csv` – `src, dst, count, sign`
- `arestas_nao_dirigidas.csv` – `src, dst, count, sign, w`
- `maior_componente.edgelist.gz` – maior componente conexa (não dirigida)

## Implementações próprias

Todos os algoritmos da Parte II, a contagem de triângulos, a clusterização, as BFS de distância,
o gerador Erdős–Rényi, o teste small-world, os ajustes de lei de potência e as métricas de robustez
estão em `src/` e são **validados contra o networkx** no notebook (seção 4.1).
Bibliotecas prontas são usadas apenas para: leitura dos dados (pandas), distâncias exatas na maior
componente e betweenness (igraph, por desempenho), PageRank e geração dos modelos BA/WS (networkx).
