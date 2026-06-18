"""
Consolida as edições do State of Data Brazil (2021–2025) num único .parquet.

A ideia aqui é a mesma que vimos em aula: em vez de ler arquivo por arquivo
na mão, a gente varre a pasta de CSVs, empilha tudo num só DataFrame e salva
no formato colunar (.parquet), que é leve e rápido de reler depois.

ENTRADA  : data/raw/State_of_Data_*.csv  (uma edição por arquivo)
SAÍDA    : data/processed/dados_state_of_data_consolidados.parquet

Rode com:  python src/coleta/consolida_state_of_data.py
"""

from pathlib import Path
import pandas as pd

# Pastas do projeto (relativas à raiz do repositório)
PASTA_RAW = Path("data/raw")
PASTA_OUT = Path("data/processed")
ARQUIVO_SAIDA = PASTA_OUT / "dados_state_of_data_consolidados.parquet"


def carregar_edicoes(pasta: Path) -> pd.DataFrame:
    """Lê todos os CSVs State_of_Data_* e empilha num só DataFrame."""
    arquivos = sorted(pasta.glob("State_of_Data_*.csv"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum CSV encontrado em {pasta}. "
            "Coloquem os arquivos State_of_Data_AAAA.csv lá."
        )

    quadros = []
    for arq in arquivos:
        print(f"  lendo {arq.name} ...")
        df = pd.read_csv(arq, low_memory=False)
        # Guardamos de qual arquivo veio cada linha — útil pra extrair o ano depois
        df["arquivo_origem"] = arq.name
        quadros.append(df)

    consolidado = pd.concat(quadros, ignore_index=True)
    print(f"  total consolidado: {len(consolidado):,} linhas")
    return consolidado


def main():
    PASTA_OUT.mkdir(parents=True, exist_ok=True)
    print("Consolidando edições do State of Data...")
    df = carregar_edicoes(PASTA_RAW)

    # (opcional) extrair o ano da pesquisa a partir do nome do arquivo
    df["ano_pesquisa"] = (
        df["arquivo_origem"].str.extract(r"(\d{4})").astype("Int64")
    )

    # Remover duplicatas exatas, se houver
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"  duplicatas removidas: {antes - len(df)}")

    df.to_parquet(ARQUIVO_SAIDA, index=False)
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    print(f"Dimensões finais: {df.shape[0]:,} linhas x {df.shape[1]:,} colunas")


if __name__ == "__main__":
    main()
