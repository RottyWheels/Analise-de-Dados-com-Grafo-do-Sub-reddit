# Análise de Dados com o Grafo de Hiperlinks entre Subreddits

Trabalho prático **"Analisando Grafos do SNAP"** – Teoria dos Grafos, IC/UFBA (Prof. Bruno Pereira dos Santos).
Matrícula **224216276** → grafo **G13 – `soc-RedditHyperlinks`** (Social networks).

- Dataset: <https://snap.stanford.edu/data/soc-RedditHyperlinks.html> (Kumar, Hamilton, Leskovec & Jurafsky, *Community Interaction and Conflict on the Web*, WWW 2018)
- Arquivo usado: `soc-redditHyperlinks-body.tsv` (hiperlinks no corpo dos posts)
- O mesmo dataset aparece na planilha como G13, G72, G92 e G109; usamos a entrada **G13**
- Checklist do trabalho: [`CHECKLIST.md`](CHECKLIST.md)

## Estrutura

```
.
├── notebook.ipynb            # orquestra os experimentos (já executado, com saídas)
├── src/
│   ├── tratamento.py         # carga do TSV e tratamento (temporal→estático, multigrafo→simples, ...)
│   ├── algoritmos.py         # BFS, DFS, Euler, Dijkstra, Bellman-Ford, Floyd-Warshall, Tarjan, Kruskal, Prim
│   ├── metricas.py           # graus, triângulos, clusterização, small-world, lei de potência
│   ├── distancias.py         # diâmetro, raio e caminho médio exatos (BFS de todos os vértices, paralela)
│   ├── centralidade.py       # betweenness (Brandes) e PageRank (iteração de potência)
│   ├── modelos.py            # geradores Barabási–Albert e Watts–Strogatz
│   ├── robustez.py           # remoção aleatória e ataque direcionado (Apêndice C)
│   ├── medicao.py            # cronometragem, IC (Normal/t-Student) e curvas de escala
│   ├── analise.py            # tabelas e casos de cada seção
│   ├── figuras.py            # gráficos do relatório
│   └── relatorio.py          # exportação: LaTeX com vírgula decimal, legenda e rótulo; PNG + PDF
├── tests/                    # pytest: implementações próprias × networkx
├── data/
│   ├── raw/download.py       # baixa o TSV original (319 MB, não versionado)
│   └── processed/            # arestas tratadas (versionadas)
├── figuras/                  # figuras em PNG e PDF
├── resultados/               # tabelas em CSV e LaTeX (.tex)
├── requirements.txt
└── pytest.ini
```

## Como executar

Requer Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m pytest                   # testes (~5 s)
python data/raw/download.py        # dados brutos (~319 MB)
jupyter notebook notebook.ipynb    # Kernel → Restart & Run All (~40 min)
```

As etapas mais demoradas são as distâncias exatas (34.671 BFS, distribuídas entre os núcleos), as curvas de
escala e as 30 repetições de robustez. `CONFERIR_IGRAPH = False` no início do notebook pula a conferência opcional
com o igraph.

## Requisitos do enunciado → onde estão

| Requisito | Notebook | Código | Saída |
|---|---|---|---|
| Cálculo de determinação do grafo | §0 | `analise.indice_grafo` | – |
| Tratamento dos dados | §2 | `tratamento.py` | `data/processed/`, `resultados/02_tratamentos` |
| **Parte I** – vértices, arestas, graus, densidade | §3 | `metricas.resumo_graus` | `resultados/03_parte1_medidas` |
| Distribuição de graus | §3 | `metricas.distribuicao_graus`, `ccdf` | `figuras/03_distribuicao_graus` |
| Componentes conexas e tamanhos | §3 | `algoritmos.componentes_conexas` | `resultados/03_tamanho_componentes` |
| Diâmetro, raio, caminho médio | §3 | `distancias.distancias_exatas` | `resultados/03_parte1_medidas` |
| Clusterização e triângulos | §3 | `metricas.triangulos_por_vertice`, `clusterizacao` | `resultados/03_parte1_medidas` |
| Visualização | §3 | `figuras.visualizacao` | `figuras/03b_visualizacao` |
| Tabela calculado / não calculado | §3 | `analise.tabela_parte1` | `resultados/03_parte1_medidas` |
| **Parte II** – BFS, DFS, Euler, Dijkstra, Bellman-Ford, Floyd-Warshall, Tarjan, Prim/Kruskal | §4.1 | `algoritmos.py` | `resultados/04_resultados_algoritmos` |
| Complexidade teórica e tempo real (média, desvio, IC) | §4.2 | `medicao.medir` | `resultados/04_tempos_execucao` |
| Complexidade observada × teórica | §4.3 | `medicao.escala` | `figuras/04_complexidade_observada`, `resultados/04_ajuste_complexidade` |
| **Parte III** – small-world (código próprio) | §5 | `metricas.small_world` | `resultados/05_small_world`, `figuras/05_small_world` |
| Lei de potência | §6 | `metricas.lei_potencia` | `resultados/06_lei_potencia`, `figuras/06_lei_potencia` |
| Robustez (aleatória e direcionada) | §7 | `robustez.py`, `centralidade.betweenness_brandes` | `resultados/07_robustez`, `figuras/07_robustez` |
| Descoberta mais interessante | §8 | `analise.tabela_hubs`, `tabela_negativos`, `centralidade.pagerank` | `resultados/08_*` |
| Extra – modelos clássicos | §9 | `modelos.py`, `metricas.erdos_renyi_gnm` | `resultados/09_modelos_classicos`, `figuras/09_modelos_ccdf` |

## Tratamento dos dados (resumo)

| Passo | Decisão |
|---|---|
| Temporal → estático | união de todos os posts (31/12/2013 a 30/04/2017) |
| Auto-loops | verificados (0 no arquivo) |
| Multigrafo → simples | uma aresta por par; `count` = nº de posts, `sign` = sinal majoritário |
| Dirigido → não dirigido | junta u→v e v→u (dirigido mantido para Tarjan, Euler dirigido e PageRank) |
| Pesos | `w = 1/count` (Dijkstra, Bellman-Ford, Floyd-Warshall, AGM) |
| Maior componente conexa | usada em distâncias, small-world e robustez |
| Subgrafos por BFS | Floyd-Warshall (O(n³)) e curvas de tempo |

Arquivos em `data/processed/`: `arestas_dirigidas.csv` (`src, dst, count, sign`), `arestas_nao_dirigidas.csv`
(`src, dst, count, sign, w`) e `maior_componente.edgelist.gz`.

## Implementações próprias e bibliotecas

Todos os algoritmos, métricas, distâncias, centralidades (Brandes, PageRank) e geradores de modelos estão em `src/`
e são testados contra o networkx em `tests/`. Bibliotecas prontas são usadas só para: leitura dos dados (pandas),
construção do grafo e validação (networkx) e conferência opcional das distâncias e do betweenness exato (igraph).

## Medição de tempo

Cada medição tem uma execução de aquecimento descartada e roda com o coletor de lixo do Python desligado.
Tempos no grafo completo: 30 repetições, IC pela Normal. Curvas de escala: 10 repetições por tamanho, IC por
t-Student, e ajuste `t ≈ c·f(n,m)` com R². Os tempos dependem da máquina; o notebook registra Python, CPU e núcleos.
