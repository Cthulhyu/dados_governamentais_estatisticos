"""
Gerador de Relatório Visual - Trabalho Final RDI
Visualização Limpa: Mapa de Calor (Heatmap) Claro.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    print("Carregando base integrada...")
    df = pd.read_parquet("data/processed/base_integrada.parquet")

    # 1. Preparação dos Dados (Pivot Table)
    df_pivot = df.pivot_table(
        index='UF_join', 
        columns='Ano_join', 
        values='Investimento_Federal_TI_R$', 
        aggfunc='sum'
    ).fillna(0)

    # 2. Ordenação Inteligente
    df_pivot['Total_Periodo'] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.sort_values(by='Total_Periodo', ascending=False)
    df_pivot = df_pivot.drop(columns=['Total_Periodo'])

    # 3. Limpeza Numérica (Convertendo para Milhões de Reais)
    df_pivot_milhoes = df_pivot / 1_000_000

    # 4. Configuração do Visual (Fundo Branco/Claro)
    # Resetamos o estilo para o padrão claro do Seaborn
    plt.style.use('default')
    sns.set_theme(style="white")
    
    fig, ax = plt.subplots(figsize=(12, 10))

    print("Gerando Mapa de Calor (Heatmap) Claro...")
    
    # 5. Criação do Heatmap
    sns.heatmap(
        df_pivot_milhoes, 
        annot=True,               
        fmt=".3f",                
        cmap="Reds",              # <-- A MÁGICA: Escala de Branco para Vermelho
        linewidths=.5,            
        linecolor='lightgray',    # Cor das linhas que separam os quadrados
        cbar_kws={'label': 'Investimento (Milhões R$)'}, 
        ax=ax
    )

    # 6. Embelezamento do Gráfico (Textos escuros para contrastar com fundo branco)
    ax.set_title('Distribuição de Investimentos Federais em TI por Estado\n(2021-2024) - Valores em Milhões', 
                 fontsize=18, pad=20, fontweight='bold', color='black')
    ax.set_ylabel('Estado (UF)', fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('Ano da Despesa', fontsize=14, fontweight='bold', color='black')

    # Remove os "ticks" para um visual mais limpo
    ax.tick_params(axis='both', which='both', length=0)

    plt.tight_layout()
    
    # 7. Salvar e Exibir garantindo o fundo branco na imagem salva
    caminho_imagem = "heatmap_investimento_ti_claro.png"
    plt.savefig(caminho_imagem, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Gráfico claro salvo com sucesso em: {caminho_imagem}")

    plt.show()

if __name__ == "__main__":
    main()