import pandas as pd
import json
import os
import re
from datetime import datetime

def parse_log_file(filepath, questionarios_set):
    """
    Analisa um único arquivo de log de conversa e extrai todas as métricas.
    """
    # --- CORREÇÃO 1: Extrair o ID correto da conversa ---
    base_filename = os.path.basename(filepath)
    conversa_id = base_filename.split('_')[0]

    data = {
        "Código da conversa": conversa_id, # <-- ID CORRIGIDO AQUI
        "Tipo de chat": None,
        "Hora inicial": None,
        "Hora final": None,
        "Tempo total": None,
        "Msg Usuário": 0,
        "Msg Bot": 0,
        "Total Mensagens": 0,
        "Contagem de Erros do Bot": 0,
        "Respondeu o questionario?": "Não",
        "Pergunta 1": "N/A",
        "Pergunta 2": "N/A",
        "Pergunta 3": "N/A",
        "Pergunta 4": "N/A",
        "Resultado Inferido": "Sucesso"
    }

    hora_inicial_dt = None
    hora_final_dt = None
    falha_detectada = False
    
    datetime_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if "Tipo de Atendimento:" in line:
                data["Tipo de chat"] = line.split(":")[1].strip()
            elif "--- Início da interação:" in line:
                match = re.search(datetime_pattern, line)
                if match:
                    timestamp_str = match.group(0)
                    hora_inicial_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    data["Hora inicial"] = hora_inicial_dt.strftime('%Y-%m-%d %H:%M:%S')
            elif "--- Fim da interação:" in line:
                match = re.search(datetime_pattern, line)
                if match:
                    timestamp_str = match.group(0)
                    hora_final_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    data["Hora final"] = hora_final_dt.strftime('%Y-%m-%d %H:%M:%S')
            elif "] Usuário:" in line:
                data["Msg Usuário"] += 1
            elif "] Bot:" in line:
                data["Msg Bot"] += 1
                
                bot_message = line.split("] Bot:")[1].strip()
                if "Não temos um item com esse número" in bot_message or \
                   "Por favor, informe apenas a quantidade em números" in bot_message or \
                   "Desculpa, não entendi" in bot_message or \
                   "Número inválido" in bot_message:
                    data["Contagem de Erros do Bot"] += 1
                
                if "não entendi o que você quis dizer" in bot_message.lower() or \
                   "não tenho como saber" in bot_message.lower() or \
                   "não tenho como te dar essa resposta" in bot_message.lower():
                     data["Contagem de Erros do Bot"] += 1

                if "atendimento está encerrado" in bot_message.lower():
                    falha_detectada = True

    data["Total Mensagens"] = data["Msg Usuário"] + data["Msg Bot"]
    if hora_inicial_dt and hora_final_dt:
        tempo_total_delta = hora_final_dt - hora_inicial_dt
        data["Tempo total"] = str(tempo_total_delta)

    if falha_detectada:
        data["Resultado Inferido"] = "Falha"
    elif data["Contagem de Erros do Bot"] > 0:
        data["Resultado Inferido"] = "Sucesso com Erros"
    else:
        data["Resultado Inferido"] = "Sucesso"
        
    # --- CORREÇÃO 2: Nova lógica para encontrar o arquivo de questionário ---
    found_questionario_file = None
    for q_filename in questionarios_set:
        # Verifica se o ID da conversa (ex: 'b2n8m3q') está contido no nome do arquivo do questionário
        if conversa_id in q_filename:
            found_questionario_file = q_filename
            break # Para a busca assim que encontrar o primeiro correspondente

    if found_questionario_file:
        data["Respondeu o questionario?"] = "Sim"
        questionario_path = os.path.join(os.path.dirname(filepath).replace('conversations', 'questionarios'), found_questionario_file)
        if os.path.exists(questionario_path):
            parse_questionnaire_file(questionario_path, data)
    # --- FIM DA CORREÇÃO ---

    return data

def parse_questionnaire_file(filepath, data):
    """
    Analisa um arquivo de questionário e atualiza o dicionário de dados da conversa.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
            p1_block = content.split("Pergunta 1:")[1].split("Pergunta 2:")[0]
            data["Pergunta 1"] = p1_block.split("Resposta:")[1].strip()
        except IndexError: pass
        
        try:
            p2_block = content.split("Pergunta 2:")[1].split("Pergunta 3:")[0]
            data["Pergunta 2"] = p2_block.split("Resposta:")[1].strip()
        except IndexError: pass
            
        # --- INÍCIO DA CORREÇÃO ---
        try:
            # Ajustado para usar o delimitador correto "Pergunta 4 (Feedback):"
            p3_block = content.split("Pergunta 3:")[1].split("Pergunta 4 (Feedback):")[0]
            data["Pergunta 3"] = p3_block.split("Resposta:")[1].strip()
        except IndexError: pass
        # --- FIM DA CORREÇÃO ---
            
        try:
            p4_block = content.split("Pergunta 4 (Feedback):")[1]
            data["Pergunta 4"] = p4_block.split("Resposta:")[1].strip()
        except IndexError: pass

def main():
    print("Iniciando análise dos logs...")

    logs_base_path = os.path.join('..', 'Back-end', 'logs')
    conversations_path = os.path.join(logs_base_path, 'conversations')
    
    log_list_file = os.path.join(logs_base_path, 'log-list.json')
    questionario_list_file = os.path.join(logs_base_path, 'questionario-list.json')

    try:
        with open(log_list_file, 'r', encoding='utf-8') as f:
            conversation_files = json.load(f)
        with open(questionario_list_file, 'r', encoding='utf-8') as f:
            questionario_files = json.load(f)
    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado - {e}.")
        print("Verifique se os caminhos no script estão corretos e se os arquivos JSON existem em 'Back-end/logs/'.")
        return

    questionarios_set = set(questionario_files)
    all_conversation_data = []

    for filename in conversation_files:
        filepath = os.path.join(conversations_path, filename)
        if os.path.exists(filepath):
            print(f"Processando: {filename}")
            data = parse_log_file(filepath, questionarios_set)
            all_conversation_data.append(data)
        else:
            print(f"AVISO: Arquivo de log não encontrado em {filepath}")

    if not all_conversation_data:
        print("Nenhum dado foi processado. Verifique os caminhos e os arquivos JSON.")
        return

    df = pd.DataFrame(all_conversation_data)
    df = df.sort_values(by='Hora inicial', ascending=False, ignore_index=True)

    colunas_ordenadas = [
        "Código da conversa", "Tipo de chat", "Hora inicial", "Hora final", "Tempo total", 
        "Msg Usuário", "Msg Bot", "Total Mensagens", "Contagem de Erros do Bot", 
        "Resultado Inferido", "Respondeu o questionario?", "Pergunta 1", 
        "Pergunta 2", "Pergunta 3", "Pergunta 4"
    ]
    df = df[colunas_ordenadas]

    output_filename = 'analise_consolidada.xlsx'
    try:
        df.to_excel(output_filename, index=False)
        print(f"\nAnálise concluída com sucesso! Planilha salva como '{output_filename}' na pasta 'Analise_de_dados'.")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar a planilha: {e}")

if __name__ == '__main__':
    main()