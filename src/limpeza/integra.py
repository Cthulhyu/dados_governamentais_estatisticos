"""
Limpeza, padronização e INTEGRAÇÃO das duas bases.

Aqui acontece o coração analítico do trabalho: pegar a base estruturada
(State of Data, já consolidada em .parquet) e a base externa coletada,
limpar as duas, e cruzá-las de forma que faça sentido para a pergunta
de pesquisa do grupo.

ENTRADAS:
  data/processed/dados_state_of_data_consolidados.parquet
  data/raw/base_externa.csv
SAÍDA:
  data/processed/base_integrada.parquet

Rode com:  python src/limpeza/integra.py
"""

from pathlib import Path
import pandas as pd

PROC = Path("data/processed")
RAW = Path("data/raw")


def ler_parquet_robusto(caminho: Path) -> pd.DataFrame:
    """Lê parquet contornando incompatibilidades pandas/pyarrow conhecidas."""
    caminho = str(caminho)
    try:
        import pyarrow.parquet as pq
        return pq.read_table(caminho).to_pandas()
    except Exception:
        pass
    try:
        return pd.read_parquet(caminho, engine="fastparquet")
    except Exception:
        return pd.read_parquet(caminho)


def main():
    print("Carregando as duas bases...")
    df_sod = ler_parquet_robusto(PROC / "dados_state_of_data_consolidados.parquet")
    df_ext = pd.read_csv(RAW / "base_externa.csv")

    print(f"  State of Data: {df_sod.shape}")
    print(f"  Base externa:  {df_ext.shape}")

    # >>> ADAPTEM: a chave e a lógica de integração dependem da pergunta de vocês.
    #     Exemplos possíveis: join por UF/região, por cargo, por faixa salarial,
    #     ou um cruzamento analítico (agregar uma base e comparar com a outra).
    #     Deixem aqui o tratamento e a integração que fizerem sentido. <<<

    base_integrada = df_sod  # placeholder — troquem pela integração real

    PROC.mkdir(parents=True, exist_ok=True)
    saida = PROC / "base_integrada.parquet"
    base_integrada.to_parquet(saida, index=False)
    print(f"Arquivo gerado: {saida}")


if __name__ == "__main__":
    main()
