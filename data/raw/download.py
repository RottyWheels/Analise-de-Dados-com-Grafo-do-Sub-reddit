"""Baixa o soc-redditHyperlinks-body.tsv (~319 MB) do SNAP para esta pasta.

Uso:  python data/raw/download.py
"""
import urllib.request
from pathlib import Path

URL = "https://snap.stanford.edu/data/soc-redditHyperlinks-body.tsv"
DESTINO = Path(__file__).with_name("soc-redditHyperlinks-body.tsv")
TAMANHO = 318_931_394  # bytes informados pelo servidor


def progresso(blocos, tam_bloco, total):
    feito = blocos * tam_bloco
    print(f"\r{feito / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)


if __name__ == "__main__":
    if DESTINO.exists() and DESTINO.stat().st_size == TAMANHO:
        print(f"Já existe: {DESTINO}")
    else:
        print(f"Baixando {URL}")
        urllib.request.urlretrieve(URL, DESTINO, progresso)
        print(f"\nSalvo em {DESTINO} ({DESTINO.stat().st_size} bytes)")
