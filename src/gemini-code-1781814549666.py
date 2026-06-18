"""
Limpeza, padronização e INTEGRAÇÃO das duas bases (SÉRIE TEMPORAL BLINDADA).
"""

from pathlib import Path
import pandas as pd

PROC = Path("data/processed")
RAW = Path("data/raw")

def ler_parquet_robusto(caminho: Path) -> pd.DataFrame:
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

def tratar_despesas_governo(df_ext: pd.DataFrame) -> pd.DataFrame:
    print("  Iniciando tratamento das despesas...")
    col_sub = [c for c in df_ext.columns if 'SUBFUN' in c.upper() or 'ROTULO' in c.upper()]
    if col_sub:
        df_ext = df_ext[df_ext[col_sub[0]].astype(str).str.contains('Tecnologia|Informa|Sistemas|Comput', case=False, na=False)]

    colunas_uf = [c for c in df_ext.columns if 'FAVORECIDO' in c.upper() and 'UF' in c.upper()]
    if not colunas_uf:
        colunas_uf = [c for c in df_ext.columns if 'UF' in c.upper()]
    col_uf = colunas_uf[0] if colunas_uf else df_ext.columns[0]

    colunas_ano = [c for c in df_ext.columns if 'ANO' in c.upper() and ('M' in c.upper() or 'LAN' in c.upper())]
    if not colunas_ano:
        colunas_ano = [c for c in df_ext.columns if 'ANO' in c.upper() or 'DATA' in c.upper()]
    
    col_ano_alvo = colunas_ano[0]
    df_ext['Ano_join'] = df_ext[col_ano_alvo].astype(str).str.extract(r'(20\d{2})')[0]
    df_ext['Ano_join'] = pd.to_numeric(df_ext['Ano_join'], errors='coerce').astype('Int64')

    colunas_valor = [c for c in df_ext.columns if 'VALOR' in c.upper() and ('LIQUID' in c.upper() or 'PAGO' in c.upper())]
    col_valor = colunas_valor[0] if colunas_valor else [c for c in df_ext.columns if 'VALOR' in c.upper()][0]
    
    df_ext['Valor_Limpo'] = (
        df_ext[col_valor]
        .astype(str)
        .str.replace(r'[^\d,]', '', regex=True) 
        .str.replace(',', '.', regex=False)
    )
    df_ext['Valor_Limpo'] = pd.to_numeric(df_ext['Valor_Limpo'], errors='coerce').fillna(0)

    df_ext['UF_join'] = df_ext[col_uf].astype(str).str.strip().str.upper()
    df_ext = df_ext[df_ext['UF_join'].str.len() == 2]

    df_agrupado = df_ext.groupby(['UF_join', 'Ano_join'])['Valor_Limpo'].sum().reset_index()
    df_agrupado.rename(columns={'Valor_Limpo': 'Investimento_Federal_TI_R$'}, inplace=True)
    return df_agrupado

def tratar_state_of_data(df_sod: pd.DataFrame) -> pd.DataFrame:
    print("  Iniciando tratamento do State of Data...")
    df_sod.columns = [str(c) for c in df_sod.columns]
    
    col_uf = [col for col in df_sod.columns if 'uf onde mora' in col.lower() or 'estado onde mora' in col.lower()][0]
    df_sod['UF_raw'] = df_sod[col_uf].astype(str).str.strip().str.upper()
    df_sod['UF_join'] = df_sod['UF_raw'].str.extract(r'\(([A-Z]{2})\)', expand=False).fillna(df_sod['UF_raw']).str[:2]
    
    col_ano = [col for col in df_sod.columns if 'ano' in col.lower() and 'pesquisa' in col.lower()]
    if col_ano:
        df_sod['Ano_join'] = pd.to_numeric(df_sod[col_ano[0]], errors='coerce').astype('Int64')
    else:
        df_sod['Ano_join'] = pd.NA
    
    df_agrupado = df_sod.groupby(['UF_join', 'Ano_join']).size().reset_index(name='Qtd_Profissionais_SoD')
    return df_agrupado

def main():
    print("Carregando bases históricas...")
    df_sod = ler_parquet_robusto(PROC / "dados_state_of_data_consolidados.parquet")
    df_ext = pd.read_csv(RAW / "base_externa.csv", low_memory=False)

    df_despesas_agg = tratar_despesas_governo(df_ext)
    df_sod_agg = tratar_state_of_data(df_sod)

    print("  Realizando a integração (OUTER Merge Temporal)...")
    base_integrada = pd.merge(df_sod_agg, df_despesas_agg, on=['UF_join', 'Ano_join'], how='outer')
    
    base_integrada['Investimento_Federal_TI_R$'] = base_integrada['Investimento_Federal_TI_R$'].fillna(0)
    base_integrada['Qtd_Profissionais_SoD'] = base_integrada['Qtd_Profissionais_SoD'].fillna(0)
    
    base_integrada['Gasto_Federal_TI_por_Profissional_R$'] = base_integrada.apply(
        lambda row: round(row['Investimento_Federal_TI_R$'] / row['Qtd_Profissionais_SoD'], 2) 
        if row['Qtd_Profissionais_SoD'] > 0 else 0.00, axis=1
    )
    
    base_integrada = base_integrada.dropna(subset=['Ano_join'])
    base_integrada = base_integrada.sort_values(by=['Ano_join', 'Investimento_Federal_TI_R$'], ascending=[True, False])

    saida = PROC / "base_integrada.parquet"
    base_integrada.to_parquet(saida, index=False)
    print(f"\nArquivo gerado e SOBRESCRITO com sucesso em: {saida}")

if __name__ == "__main__":
    main()