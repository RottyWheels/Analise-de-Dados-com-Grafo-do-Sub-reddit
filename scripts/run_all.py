"""Executa o trabalho inteiro sem abrir o Jupyter: testes, conferência dos dados e notebook.

Uso:  python scripts/run_all.py            (~40 min; grava o notebook executado no lugar)
      python scripts/run_all.py --sem-notebook
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def rodar(*cmd):
    print("\n$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode:
        sys.exit(r.returncode)


if __name__ == "__main__":
    py = sys.executable
    if not (RAIZ / "data/raw/soc-redditHyperlinks-body.tsv").exists():
        rodar(py, "data/raw/download.py")
    rodar(py, "scripts/verificar_dados.py")
    rodar(py, "-m", "pytest", "tests")
    if "--sem-notebook" not in sys.argv:
        rodar(py, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
              "--ExecutePreprocessor.timeout=-1", "notebook.ipynb")
        print("\nPronto: notebook.ipynb, figuras/ e resultados/ atualizados.")
