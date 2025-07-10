import pandas as pd
import os

def clean_and_prepare_data(df):
    """Converte colunas para os tipos corretos e normaliza os dados."""
    # Converte a coluna de tempo (string) para segundos (numérico)
    df['Tempo total (s)'] = pd.to_timedelta(df['Tempo total'], errors='coerce').dt.total_seconds()
    
    # Converte a coluna da Pergunta 1 para numérico
    df['Pergunta 1 num'] = pd.to_numeric(df['Pergunta 1'], errors='coerce')
    
    # Normaliza respostas de texto para minúsculas
    for col in ['Pergunta 2', 'Pergunta 3']:
        df[col] = df[col].str.lower()
        
    return df

def format_seconds_to_ms(seconds):
    """Formata um valor em segundos para o formato MM:SS."""
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"

def generate_text_summary(df):
    """Gera um resumo de texto completo com todas as estatísticas solicitadas."""
    
    report_lines = []
    
    # Filtra os dataframes por tipo de chat
    df_trad = df[df['Tipo de chat'] == 'tradicional']
    df_intel = df[df['Tipo de chat'] == 'inteligente']

    separator = "="*60
    report_lines.append(separator)
    report_lines.append(" RELATÓRIO GERAL DE DADOS DE ATENDIMENTO")
    report_lines.append(separator)
    
    # Métricas Globais
    total_conversas = len(df)
    total_mensagens = int(df['Total Mensagens'].sum())
    total_questionarios = df[df['Respondeu o questionario?'] == 'Sim'].shape[0]
    
    report_lines.append("\n--- Métricas Gerais ---")
    report_lines.append(f"Total de conversas analisadas: {total_conversas}")
    report_lines.append(f"Total de mensagens trocadas: {total_mensagens}")
    report_lines.append(f"Total de questionários respondidos: {total_questionarios}")

    report_lines.append("\n\n" + separator)
    report_lines.append(" ANÁLISE COMPARATIVA POR TIPO DE CHATBOT")
    report_lines.append(separator)

    # Tempo médio de conversa
    tempo_medio_trad_s = df_trad['Tempo total (s)'].mean()
    tempo_medio_intel_s = df_intel['Tempo total (s)'].mean()
    report_lines.append("\n--- Tempo Médio de Conversa (MM:SS) ---")
    report_lines.append(f"Chatbot Tradicional: {format_seconds_to_ms(tempo_medio_trad_s)}")
    report_lines.append(f"Chatbot Inteligente: {format_seconds_to_ms(tempo_medio_intel_s)}")

    # Índice de falha
    erros_trad = int(df_trad['Contagem de Erros do Bot'].sum())
    msgs_bot_trad = int(df_trad['Msg Bot'].sum())
    taxa_erro_trad = (erros_trad / msgs_bot_trad * 100) if msgs_bot_trad > 0 else 0

    erros_intel = int(df_intel['Contagem de Erros do Bot'].sum())
    msgs_bot_intel = int(df_intel['Msg Bot'].sum())
    taxa_erro_intel = (erros_intel / msgs_bot_intel * 100) if msgs_bot_intel > 0 else 0
    report_lines.append("\n--- Índice de Falha do Bot ---")
    report_lines.append(f"Chatbot Tradicional: {erros_trad}/{msgs_bot_trad} ({taxa_erro_trad:.2f}%)")
    report_lines.append(f"Chatbot Inteligente: {erros_intel}/{msgs_bot_intel} ({taxa_erro_intel:.2f}%)")

    # Helper para criar tabelas de resumo
    def create_summary_df(series):
        if series.dropna().empty:
            return "Nenhum dado para exibir."
        counts = series.value_counts()
        percentages = series.value_counts(normalize=True).mul(100).round(2)
        summary_df = pd.DataFrame({'Contagem': counts, 'Percentual (%)': percentages})
        return summary_df.to_string()

    report_lines.append("\n--- Pergunta 1: Nível de Satisfação (Estrelas) ---")
    report_lines.append("\n[Chatbot Tradicional]")
    report_lines.append(create_summary_df(df_trad['Pergunta 1 num'].dropna().sort_index()))
    report_lines.append("\n[Chatbot Inteligente]")
    report_lines.append(create_summary_df(df_intel['Pergunta 1 num'].dropna().sort_index()))

    report_lines.append("\n\n--- Pergunta 2: Conseguiu Realizar o que Desejava? ---")
    report_lines.append("\n[Chatbot Tradicional]")
    report_lines.append(create_summary_df(df_trad['Pergunta 2'].dropna()))
    report_lines.append("\n[Chatbot Inteligente]")
    report_lines.append(create_summary_df(df_intel['Pergunta 2'].dropna()))
        
    report_lines.append("\n\n--- Pergunta 3: Preferência (Chatbot vs. Atendimento Humano) ---")
    
    # Análise para o Bot Tradicional
    pref_trad_series = df_trad['Pergunta 3'].dropna()
    report_lines.append("\n[Grupo do Chatbot Tradicional]")
    report_lines.append(create_summary_df(pref_trad_series))

    # Análise para o Bot Inteligente
    pref_intel_series = df_intel['Pergunta 3'].dropna()
    report_lines.append("\n[Grupo do Chatbot Inteligente]")
    report_lines.append(create_summary_df(pref_intel_series))
    
    # Análise Comparativa da Taxa de Aceitação
    report_lines.append("\n[Análise da Aceitação Relativa dos Chatbots]")
    try:
        aceitacao_trad = pref_trad_series.value_counts(normalize=True).get('usaria o chatbot', 0) * 100
        aceitacao_intel = pref_intel_series.value_counts(normalize=True).get('usaria o chatbot', 0) * 100
        report_lines.append(f"Taxa de aceitação do bot Tradicional (vs. humano): {aceitacao_trad:.2f}%")
        report_lines.append(f"Taxa de aceitação do bot Inteligente (vs. humano): {aceitacao_intel:.2f}%")
    except Exception as e:
        report_lines.append(f"Não foi possível calcular a aceitação relativa: {e}")    

    report_lines.append("\n\n" + separator)
    
    return "\n".join(report_lines)

def main():
    """Função principal para carregar dados e gerar o relatório de texto."""
    
    print("Iniciando geração do relatório...")
    
    input_filename = 'analise_consolidada.xlsx'
    output_filename = 'relatorio_final.txt'

    try:
        print(f"Carregando dados de '{input_filename}'...")
        df = pd.read_excel(input_filename)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{input_filename}' não encontrado.")
        print("Por favor, execute o script 'analise_dados.py' primeiro.")
        return
    
    print("Processando e calculando estatísticas...")
    df_prepared = clean_and_prepare_data(df)
    
    # Gera o conteúdo do relatório
    report_content = generate_text_summary(df_prepared)
    
    # Salva o relatório em um arquivo .txt
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"\nRelatório salvo com sucesso no arquivo: '{output_filename}'")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar o arquivo de relatório: {e}")
        
    # Imprime o relatório no terminal
    print("\n--- INÍCIO DO RELATÓRIO ---")
    print(report_content)
    print("--- FIM DO RELATÓRIO ---")


if __name__ == '__main__':
    main()