"""
Consolida as edições do State of Data Brazil (2021–2025) num único .parquet.
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
        
        # O .copy() resolve o PerformanceWarning de fragmentação de memória do Pandas
        df = df.copy() 
        
        df["arquivo_origem"] = arq.name
        quadros.append(df)

    consolidado = pd.concat(quadros, ignore_index=True)
    print(f"  total consolidado: {len(consolidado):,} linhas")
    return consolidado


def main():
    PASTA_OUT.mkdir(parents=True, exist_ok=True)
    print("Consolidando edições do State of Data...")
    df = carregar_edicoes(PASTA_RAW)

    # Extrair o ano da pesquisa a partir do nome do arquivo
    df["ano_pesquisa"] = (
        df["arquivo_origem"].str.extract(r"(\d{4})").astype("Int64")
    )

    # Remover duplicatas exatas, se houver
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"  duplicatas removidas: {antes - len(df)}")

    # =========================================================
    # CORREÇÃO PARA O ERRO DO PYARROW (TIPOS MISTOS)
    # =========================================================
    print("  Padronizando tipos de dados para conversão Parquet...")
    
    # 1. Garante que os nomes de todas as colunas sejam strings
    df.columns = df.columns.astype(str)
    
    # 2. Converte todas as colunas com tipos de dados mistos (object) para texto (string).
    # Isso impede que o Parquet trave ao ver 'True' em um ano e '1' no outro.
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)

    print("  Salvando arquivo...")
    df.to_parquet(ARQUIVO_SAIDA, index=False)
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    print(f"Dimensões finais: {df.shape[0]:,} linhas x {df.shape[1]:,} colunas")


if __name__ == "__main__":
    main()