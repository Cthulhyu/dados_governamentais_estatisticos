from pathlib import Path
from zipfile import ZipFile
import requests
import pandas as pd

PASTA_RAW = Path("data/raw")
ARQUIVO_SAIDA = PASTA_RAW / "base_externa.csv"

URL = (
    "https://dadosabertos-download.cgu.gov.br/"
    "PortalDaTransparencia/saida/despesas-execucao/"
    "202501_Despesas.zip"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def baixar_zip():
    print("Baixando arquivo...")

    resp = requests.get(
        URL,
        headers=HEADERS,
        stream=True,
        timeout=300
    )

    print("Status HTTP:", resp.status_code)

    resp.raise_for_status()

    zip_path = PASTA_RAW / "despesas.zip"

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    return zip_path


def ler_zip(zip_path):
    print("Extraindo ZIP...")

    with ZipFile(zip_path) as z:

        arquivos_csv = [
            arq
            for arq in z.namelist()
            if arq.lower().endswith(".csv")
        ]

        print("Arquivos encontrados:")
        for arq in arquivos_csv:
            print(" -", arq)

        if not arquivos_csv:
            raise Exception("Nenhum CSV encontrado.")

        csv_file = arquivos_csv[0]

        print("Lendo:", csv_file)

        with z.open(csv_file) as f:

            try:
                df = pd.read_csv(
                    f,
                    sep=";",
                    encoding="latin1",
                    low_memory=False
                )
            except Exception:
                f.seek(0)

                df = pd.read_csv(
                    f,
                    sep=";",
                    encoding="utf-8",
                    low_memory=False
                )

    return df


def tratar(df):
    print("Linhas:", len(df))
    print("Colunas:", len(df.columns))

    print("\nPrimeiras colunas:")
    print(df.columns.tolist()[:20])

    return df


def main():
    PASTA_RAW.mkdir(
        parents=True,
        exist_ok=True
    )

    zip_path = baixar_zip()

    df = ler_zip(zip_path)

    df = tratar(df)

    df.to_csv(
        ARQUIVO_SAIDA,
        index=False
    )

    print(f"\nArquivo gerado: {ARQUIVO_SAIDA}")
    print(df.shape)


if __name__ == "__main__":
    main()