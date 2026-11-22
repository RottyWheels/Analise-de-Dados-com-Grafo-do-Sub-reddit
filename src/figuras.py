"""Figuras do relatório. Cada função recebe dados já calculados, desenha e salva (PNG + PDF)."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from . import metricas as M
from .relatorio import salvar_figura

AZUL, LARANJA, VERDE, ROXO, CINZA = "#2a6fdb", "#e76f51", "#2a9d8f", "#7b2cbf", "#9aa5b1"


def estilo():
    plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.formatter.use_locale": False})


def original(df):
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
    df.set_index("ts").resample("ME")["sign"].count().plot(ax=ax[0], color=AZUL)
    ax[0].set(title="Posts com link por mês", xlabel="", ylabel="posts")
    df["sign"].value_counts().rename({1: "+1", -1: "−1"}).plot.bar(ax=ax[1], color=[VERDE, LARANJA], rot=0)
    ax[1].set(title="Sinal dos links", ylabel="posts")
    return salvar_figura(fig, "01_original_tempo_sinal")


def distribuicao_graus(adj):
    graus = [len(v) for v in adj.values()]
    kc, pc = M.ccdf(adj)
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    ax[0].hist(graus, bins=np.logspace(0, np.log10(max(graus)), 40), color=AZUL)
    ax[0].set(xscale="log", yscale="log", title="Histograma de graus (bins log)", xlabel="grau k",
              ylabel="nº de vértices")
    ax[1].loglog(kc, pc, ".", ms=3, color=LARANJA)
    ax[1].set(title="CCDF  P(K ≥ k)", xlabel="grau k", ylabel="P(K ≥ k)")
    return salvar_figura(fig, "03_distribuicao_graus")


def visualizacao(G, top: int = 150, rotulos: int = 12):
    import networkx as nx
    nos = [u for u, _ in sorted(G.degree, key=lambda x: -x[1])[:top]]
    H = G.subgraph(nos)
    H = H.subgraph(max(nx.connected_components(H), key=len))
    pos = nx.kamada_kawai_layout(H, weight=None)
    deg = dict(H.degree)
    cores = [LARANJA if d["sign"] < 0 else CINZA for *_, d in H.edges(data=True)]
    fig, ax = plt.subplots(figsize=(10, 10))
    nx.draw_networkx_edges(H, pos, edge_color=cores, alpha=0.25, width=0.4, ax=ax)
    nx.draw_networkx_nodes(H, pos, node_size=[5 + deg[u] * 1.5 for u in H], node_color=AZUL, alpha=0.8, ax=ax)
    lab = {u: u for u in sorted(H, key=lambda u: -G.degree[u])[:rotulos]}
    nx.draw_networkx_labels(H, pos, lab, font_size=8, font_weight="bold",
                            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5), ax=ax)
    ax.set_title(f"Subgrafo dos {top} subreddits de maior grau ({H.number_of_nodes()} vértices, "
                 f"{H.number_of_edges()} arestas)\narestas laranja = sinal negativo")
    ax.axis("off")
    return salvar_figura(fig, "03b_visualizacao")


def escala(df):
    """Tempo médio com IC (t-Student) por tamanho e curva c·f(n,m) ajustada."""
    algs = list(dict.fromkeys(df["algoritmo"]))
    col = 4
    lin = -(-len(algs) // col)
    fig, axs = plt.subplots(lin, col, figsize=(4 * col, 3.2 * lin))
    axs = np.atleast_1d(axs).ravel()
    for ax, nome in zip(axs, algs):
        d = df[df["algoritmo"] == nome].sort_values("n")
        err = [d["media_s"] - d["ic_inf_s"], d["ic_sup_s"] - d["media_s"]]
        ax.errorbar(d["n"], d["media_s"], yerr=err, fmt="o-", ms=4, capsize=3, color=AZUL, label="observado (IC 95%)")
        ax.plot(d["n"], d["previsto_s"], "--", color=LARANJA, label=f"c·f(n,m)  R²={d['r2_ajuste'].iloc[0]:.3f}")
        if "previsto_alt_s" in d and d["previsto_alt_s"].notna().any():
            ax.plot(d["n"], d["previsto_alt_s"], ":", color=VERDE, label="c·k·m (parada antecipada)")
        ax.set(title=nome, xlabel="n (vértices)", ylabel="tempo (s)")
        ax.legend(fontsize=7)
    for ax in axs[len(algs):]:
        ax.axis("off")
    fig.tight_layout()
    return salvar_figura(fig, "04_complexidade_observada")


def small_world(sw, swg=None):
    """Barras de C e L: G13 × G(n, m) e, se dado, × nulo que preserva os graus."""
    rot, cores = ["G13", "G(n,m)"], [AZUL, CINZA]
    C, L = [sw["C(G)"], sw["C_aleatorio"]], [sw["L(G)"], sw["L_aleatorio"]]
    if swg:
        rot.append("mesmos graus"); cores.append(VERDE)
        C.append(swg["C_graus"]); L.append(swg["L_graus"])
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].bar(rot, C, color=cores)
    ax[0].set(title="Clusterização média C (escala log)", yscale="log")
    ax[1].bar(rot, L, color=cores)
    ax[1].set(title="Comprimento médio dos caminhos L")
    return salvar_figura(fig, "05_small_world")


def lei_potencia(adj, pl, grau_medio):
    from scipy.stats import poisson
    ks, pk = M.distribuicao_graus(adj)
    kc, pc = M.ccdf(adj)
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].loglog(ks, pk, ".", ms=4, color=AZUL, label="observado")
    xx = np.array([ks.min(), ks.max()], float)
    ax[0].loglog(xx, 10 ** pl["logC_pk"] * xx ** (-pl["gamma_pk"]), "r--",
                 label=f"regressão P(k) bruto: γ={pl['gamma_pk']:.2f} (R²={pl['r2_pk']:.2f})")
    ax[0].loglog(xx, 10 ** pl["logC_pk_bins_log"] * xx ** (-pl["gamma_pk_bins_log"]), "-", color=VERDE, lw=1,
                 label=f"regressão bins log: γ={pl['gamma_pk_bins_log']:.2f} (R²={pl['r2_pk_bins_log']:.2f})")
    kk = np.arange(1, 60)
    ax[0].loglog(kk, poisson.pmf(kk, grau_medio), ":", color="gray", label=f"Poisson (ER) λ={grau_medio:.1f}")
    ax[0].set(title="log P(k) × log k", xlabel="k", ylabel="P(k)", ylim=(pk.min() / 2, 1))
    ax[0].legend(fontsize=7)
    ax[1].loglog(kc, pc, ".", ms=4, color=LARANJA, label="CCDF observada")
    km = pl["kmin_mle"]
    xs = np.array([km, kc.max()], float)
    p_km = pc[np.searchsorted(kc, km)]
    ax[1].loglog(xs, p_km * (xs / km) ** (1 - pl["gamma_mle"]), "k--",
                 label=f"MLE: γ={pl['gamma_mle']:.2f}, k_min={km}")
    ax[1].set(title="CCDF  P(K ≥ k)", xlabel="k")
    ax[1].legend(fontsize=7)
    return salvar_figura(fig, "06_lei_potencia")


def robustez(orig, aleat, ataques: dict):
    nomes = {"A_S": "A – maior componente (S)", "B_c": "B – nº de componentes (c)",
             "C_L": "C – caminho médio (L)", "D_isolados": "D – fração de isolados"}
    estilos = [(LARANJA, "--"), (ROXO, "-."), (VERDE, (0, (1, 1)))]
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.6))
    for ax, (k, t) in zip(axs, nomes.items()):
        ax.boxplot(aleat[k], widths=0.5)
        ax.errorbar([1.35], [aleat[k].mean()], yerr=[aleat[k].std()], fmt="o", color="k", capsize=4,
                    label="aleatória: média ± dp")
        ax.axhline(orig[k], color="gray", ls=":", label="original")
        for (nome, res), (cor, ls) in zip(ataques.items(), estilos):
            ax.axhline(res[k], color=cor, ls=ls, label=nome)
        ax.set(title=t, xticks=[1], xticklabels=["aleatória (30×)"])
    axs[0].legend(fontsize=7)
    fig.tight_layout()
    return salvar_figura(fig, "07_robustez")


def modelos_ccdf(modelos: dict):
    fig, ax = plt.subplots(figsize=(6, 4))
    for nome, a in modelos.items():
        k_, p_ = M.ccdf(a)
        ax.loglog(k_, p_, ".", ms=3, label=nome)
    ax.set(title="CCDF dos graus: G13 × modelos clássicos", xlabel="k", ylabel="P(K ≥ k)")
    ax.legend(fontsize=7)
    return salvar_figura(fig, "09_modelos_ccdf")
