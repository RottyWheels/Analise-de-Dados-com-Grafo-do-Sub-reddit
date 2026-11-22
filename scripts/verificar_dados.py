"""Confere o arquivo bruto contra as contagens esperadas (tamanho e grafo tratado).

Uso:  python scripts/verificar_dados.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import tratamento as T  # noqa: E402

ESPERADO = {
    "bytes": 318_931_394,
    "posts (linhas)": 286_561,
    "subreddits distintos": 35_776,
    "pares dirigidos distintos": 137_821,
    "arestas não dirigidas": 124_330,
    "auto-loops": 0,
}


def main() -> int:
    caminho = RAIZ / "data/raw/soc-redditHyperlinks-body.tsv"
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}\nRode antes: python data/raw/download.py")
        return 1
    df = T.carregar_bruto(caminho)
    d = T.descrever_bruto(df)
    obtido = {
        "bytes": caminho.stat().st_size,
        "posts (linhas)": d["posts (linhas)"],
        "subreddits distintos": d["subreddits distintos"],
        "pares dirigidos distintos": d["pares dirigidos distintos"],
        "arestas não dirigidas": len(T.arestas_nao_dirigidas(T.arestas_dirigidas(df))),
        "auto-loops": d["auto-loops"],
    }
    ok = True
    for k, esperado in ESPERADO.items():
        bate = obtido[k] == esperado
        ok &= bate
        print(f"{'OK ' if bate else 'ERRO'} {k:28s} esperado {esperado:>12,}  obtido {obtido[k]:>12,}")
    print("Dados conferem." if ok else "Os dados NÃO conferem com o esperado.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
