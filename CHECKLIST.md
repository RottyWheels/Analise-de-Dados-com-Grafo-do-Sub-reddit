# Checklist — TP Analisando Grafos do SNAP

**Disciplina:** Teoria dos Grafos — IC/UFBA · Prof. Bruno Pereira dos Santos
**Matrícula:** 224216276 → **G13 – soc-RedditHyperlinks** (Social networks)
**Dataset:** https://snap.stanford.edu/data/soc-RedditHyperlinks.html — arquivo usado: `soc-redditHyperlinks-body.tsv`
**Entrega:** `224216276.pdf` no Moodle (template WebMedia/Overleaf) + link deste repositório

> Status em 22/11/2026: código, testes, notebook, dados e relatório (relatorio/224216276.pdf) prontos.
> Falta: revisar o texto, compilar no Overleaf, testar o README e enviar no Moodle.
>
> Itens marcados com **[R]** devem aparecer obrigatoriamente no relatório.

---

## 0. Determinação do grafo **[R]**
- [x] Célula no notebook com o cálculo: f(M) = ((soma dos dígitos de M) × (últimos 2 dígitos de M + 1)) mod 129
  - soma = 2+2+4+2+1+6+2+7+6 = 32; últimos 2 dígitos = 76 → 32 × 77 = 2464; 2464 mod 129 = **13**
- [x] Nota no relatório: o mesmo dataset aparece como G13, G72, G92 e G109 na planilha; usada a entrada G13

## 1. Estrutura do repositório (30% da nota)
- [x] `README.md` — descrição, como instalar e como executar
- [x] `requirements.txt` (pandas, numpy, networkx, matplotlib, scipy, igraph, jupyter)
- [x] `.gitignore` (ignorar `data/raw/*.tsv`, checkpoints do Jupyter, `__pycache__`)
- [x] `data/raw/` — script de download do `.tsv` (arquivo de 319 MB > limite de 100 MB do GitHub)
- [x] `data/processed/` — listas de arestas tratadas (versionadas)
- [x] `src/` com toda a lógica: algoritmos, métricas, distâncias, centralidade, modelos, robustez, medição, tabelas e figuras
- [x] `tests/` — suíte pytest comparando as implementações próprias com networkx
- [x] Tabela "requisito → notebook/código/saída" no README
- [x] `notebook.ipynb` executável do início ao fim
- [x] `figuras/` — PNGs usados no relatório

## 2. Carga e descrição do grafo original **[R]**
- [x] Ler o TSV (SOURCE, TARGET, TIMESTAMP, LINK_SENTIMENT; descartar PROPERTIES)
- [x] Descrever o original: 286.561 posts, período 31/12/2013–30/04/2017, sinais (+1: 265.491 / −1: 21.070)
- [x] Explicar por que os números diferem da planilha (planilha = body + title)

## 3. Tratamento dos dados **[R]**
- [x] Temporal → estático (união das arestas no período)
- [x] Multigrafo → simples (atributos `count` e `sign` majoritário)
- [x] Verificar auto-loops (esperado: 0) e registrar
- [x] Gerar `G_dir` (dirigido) e `G_und` (não dirigido)
- [x] Definir pesos `w = 1/count` (Dijkstra, Prim/Kruskal)
- [x] Extrair maior componente conexa `G_lcc`
- [x] Gerar subgrafos de teste (n = 100, 250, 500, 1000, 2000) para Floyd-Warshall e medições de tempo
- [x] Tabela com todos os tratamentos e justificativas
- [x] Salvar em `data/processed/`

## 4. Parte I – Análise estrutural obrigatória **[R]**
- [x] Número de vértices
- [x] Número de arestas
- [x] Grau mínimo, máximo e médio
- [x] Distribuição de graus (histograma + CCDF)
- [x] Densidade
- [x] Número de componentes conexas
- [x] Tamanho de cada componente
- [x] Diâmetro
- [x] Raio
- [x] Comprimento médio dos caminhos
- [x] Coeficiente de clusterização médio
- [x] Número de triângulos
- [x] Visualização do grafo (versão reduzida, ex.: top ~300 vértices por grau)
- [x] **Tabela "calculado / não calculado"** com justificativa para o que faltar

## 5. Parte II – Algoritmos da disciplina **[R]**
Implementação própria em `src/algoritmos.py`, validada contra networkx.
- [x] BFS
- [x] DFS (iterativa)
- [x] Verificação de Eulerianidade (não dirigido e dirigido)
- [x] Dijkstra (se aplicável)
- [x] Bellman-Ford (se aplicável)
- [x] Floyd-Warshall (em subgrafos; justificar inviabilidade O(n³) no grafo completo)
- [x] Tarjan (componentes fortemente conexas em `G_dir`)
- [x] Prim e/ou Kruskal (árvore geradora mínima)
- [x] Complexidade teórica de cada algoritmo
- [x] Tempo real: 30 repetições → média, desvio padrão e IC
  - n ≥ 30 → Normal: x̄ ± z_{α/2} · σ/√n
  - n < 30 e σ desconhecido → t-Student: x̄ ± t_{α/2} · σ/√n
- [x] Gráfico tempo × tamanho (teórico vs. observado), com IC por tamanho (t-Student) e ajuste c·f(n,m)
- [x] Aquecimento e coletor de lixo desligado nas medições

## 6. Parte III – Análise estrutural **[R]**
### 6.1 Small-world (Apêndice A) — código próprio, sem biblioteca pronta
- [x] Calcular L(G) e C(G) em `G_lcc`
- [x] Calcular L e C de grafo aleatório equivalente (mesmo n e grau médio)
- [x] Testar: **L(G) ≈ L_aleatório** e **C(G) ≫ C_aleatório**
- [x] Responder: faz sentido para o grafo? Implicação prática?

### 6.2 Lei de potência (Apêndice B)
- [x] Distribuição de graus → histograma e/ou CCDF
- [x] Plot log-log de log(P(k)) vs log(k)
- [x] Regressão linear: log(P(k)) = −γ·log(k) + log(C) → estimar γ
- [x] Verificar se γ > 1 e se o gráfico é aproximadamente linear
- [x] (Opcional) γ por máxima verossimilhança (Clauset) para comparar

### 6.3 Robustez (Apêndice C)
- [x] Política para grafo desconexo: usar `G_lcc` (documentar)
- [x] n = |V|, r = ⌈0,05 × n⌉
- [x] Métricas: A (tamanho da maior componente), B (nº de componentes), C (distâncias), D (fração de isolados)
- [x] Remoção aleatória: 30–50 repetições + boxplots (média ± desvio)
- [x] Ataque direcionado: centralidade escolhida (grau e/ou betweenness), ranking fixo, remover top r
- [x] Comparar S_rand vs S_cent e c_rand vs c_cent
- [x] Interpretar: vulnerável se S_rand ≫ S_cent e c_cent ≫ c_rand

### 6.4 Descoberta mais interessante
- [x] Escolher e argumentar (ex.: hubs, concentração de links negativos, SCC vs WCC, reciprocidade)

### 6.5 (EXTRA) Modelo clássico
- [x] Comparar com Erdős–Rényi, Barabási–Albert e Watts–Strogatz (mesmo n e m)

## 7. Relatório (70% da nota) — template WebMedia
- [x] Cálculo de determinação do grafo
- [x] Link para o GitHub
- [x] Descrição do grafo original
- [x] Tratamento realizado
- [x] Metodologia
- [x] Resultados: tabelas e gráficos, cada um comentado
- [x] Respostas às perguntas obrigatórias (Parte III, itens 1–4)
- [x] Discussão crítica
- [x] Conclusão
- [x] PDF nomeado `224216276.pdf` (relatorio/224216276.pdf)
- [x] Preencher autor e e-mail em `relatorio/main.tex`
- [ ] Revisar o texto do relatório (interpretações com as próprias palavras)
- [ ] Compilar no Overleaf com o template WebMedia e enviar no Moodle

## 8. Revisão final
- [x] Notebook roda do zero (Kernel → Restart & Run All)
- [ ] README testado seguindo os passos
- [x] Todas as figuras do relatório estão em `figuras/`
- [x] Todos os itens **[R]** presentes no PDF
