"""
Coleta da BASE EXTERNA via Portal da Transparência (CGU).
Baixa os dados do histórico completo: de Janeiro de 2021 a Dezembro de 2024.
Aplica um pré-filtro de TI durante a extração para não estourar o disco rígido.
"""

from pathlib import Path
from zipfile import ZipFile
import requests
import pandas as pd
import os
import time

PASTA_RAW = Path("data/raw")
ARQUIVO_SAIDA = PASTA_RAW / "base_externa.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def coletar_historico(ano_inicio=2021, ano_fim=2024) -> pd.DataFrame:
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    zip_path = PASTA_RAW / "temp_despesas.zip"
    lista_dfs_meses = []
    
    print(f"Iniciando coleta histórica ({ano_inicio} a {ano_fim}). Isso pode levar um bom tempo...\n")
    
    # Loop duplo: para cada ano, passa por todos os 12 meses
    for ano in range(ano_inicio, ano_fim + 1):
        for mes in range(1, 13):
            mes_str = f"{mes:02d}"
            url = (
                "https://dadosabertos-download.cgu.gov.br/"
                f"PortalDaTransparencia/saida/despesas-execucao/{ano}{mes_str}_Despesas.zip"
            )
            
            print(f"[{mes_str}/{ano}] Baixando arquivo do Portal da Transparência...")
            try:
                # Aumentamos o timeout pois os arquivos de final de ano costumam ser gigantes
                resp = requests.get(url, headers=HEADERS, stream=True, timeout=600)
                
                if resp.status_code != 200:
                    print(f"  -> ERRO HTTP {resp.status_code}: O arquivo de {mes_str}/{ano} não está disponível ou falhou.")
                    continue
                    
                # Salva o zip temporariamente no disco
                with open(zip_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            
            except requests.exceptions.RequestException as e:
                print(f"  -> Falha na conexão para {mes_str}/{ano}: {e}. Pulando para o próximo.")
                time.sleep(5) # Pausa rápida antes de tentar o próximo para não levar bloqueio da API
                continue
                        
            print(f"[{mes_str}/{ano}] Extraindo e filtrando despesas de TI...")
            try:
                with ZipFile(zip_path) as z:
                    arquivos_csv = [arq for arq in z.namelist() if arq.lower().endswith(".csv")]
                    if arquivos_csv:
                        with z.open(arquivos_csv[0]) as f:
                            try:
                                df_mes = pd.read_csv(f, sep=";", encoding="latin1", low_memory=False)
                            except Exception:
                                f.seek(0)
                                df_mes = pd.read_csv(f, sep=";", encoding="utf-8", low_memory=False)
                            
                            # Pré-filtro inteligente para manter só TI e poupar RAM
                            col_sub = [c for c in df_mes.columns if 'SUBFUN' in c.upper() or 'ROTULO' in c.upper()]
                            if col_sub:
                                df_mes = df_mes[df_mes[col_sub[0]].astype(str).str.contains('Tecnologia|Informa|Sistemas|Comput', case=False, na=False)]
                            
                            lista_dfs_meses.append(df_mes)
                            print(f"  -> Sucesso! {len(df_mes):,} registros de TI encontrados neste mês.")
            except Exception as e:
                print(f"  -> Erro ao extrair/ler o arquivo ZIP de {mes_str}/{ano}: {e}")
    
    # Limpeza do arquivo temporário
    if zip_path.exists():
        os.remove(zip_path)
        
    print("\nConcatenando todos os 48 meses processados...")
    if lista_dfs_meses:
        df_final = pd.concat(lista_dfs_meses, ignore_index=True)
        return df_final
    else:
        return pd.DataFrame()

def main():
    # Chama a função pegando de 2021 a 2024
    df_historico = coletar_historico(ano_inicio=2021, ano_fim=2024)
    
    if not df_historico.empty:
        df_historico.to_csv(ARQUIVO_SAIDA, index=False)
        print(f"\nBase externa histórica salva com SUCESSO em {ARQUIVO_SAIDA}")
        print(f"Total de registros de despesas em TI acumulados (2021-2024): {len(df_historico):,}")
    else:
        print("\nFalha crítica: Nenhum dado foi coletado ao longo do período.")

if __name__ == "__main__":
    main()