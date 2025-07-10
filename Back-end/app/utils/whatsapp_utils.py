import logging
import random
from flask import Flask, current_app, request, jsonify
import json
import requests
import re
import os
import google.generativeai as genai
import pyodbc
from datetime import datetime, date

# Configuração do Gemini
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"credenciais_google.json"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

#model = genai.GenerativeModel('gemini-1.5-flash-latest') #500 requisições por dia e 15 por minuto
#model = genai.GenerativeModel('gemini-2.0-flash') #1000 requisições por dia e 15 por minuto
#model = genai.GenerativeModel('gemini-2.0-flash-lite') #1500 requisições por dia e 30 por minuto
#model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17') #500 requisições por dia e 15 por minuto

def get_active_model_name():
    """
    Verifica a contagem de requisições e retorna o nome do modelo apropriado
    em uma estratégia de 3 níveis para maximizar a cota diária.
    """
    global model_request_count, last_request_date

    # Lógica para resetar o contador diariamente (permanece a mesma)
    today = date.today()
    if today != last_request_date:
        model_request_count = 0
        last_request_date = today
        logging.info("Novo dia, contador de requisições do Gemini resetado.")

    # --- LÓGICA DE TROCA DE MODELO EM 3 NÍVEIS ---

    # Nível 1: Até 1500 requisições
    if model_request_count < 1500:
        # Usa o modelo principal (Alto RPM, 1500/dia)
        return 'gemini-2.0-flash-lite'
    
    # Nível 2: De 1500 até 2500 requisições
    elif model_request_count < 2500: # 1500 (nível 1) + 1000 (nível 2)
        # Usa o modelo de backup 1 (1000/dia)
        logging.warning(f"Cota do modelo principal atingida. Trocando para o backup 1: gemini-2.0-flash")
        return 'gemini-2.0-flash'
    
    # Nível 3: Acima de 2500 requisições
    else:
        # Usa o modelo de backup final (500/dia)
        logging.warning(f"Cota do backup 1 atingida. Trocando para o backup 2: gemini-1.5-flash")
        return 'gemini-1.5-flash'

model_request_count = 0
last_request_date = date.today()

chats = {}
gemini_chats = {}
customer_data = {}
historico_conversas = {}
tipo_atendimento = {}
respostas_questionario = {}

MENU_PRINCIPAL_TEXT = (
    "Olá! 😊 Que bom ter você por aqui! *Por favor, escolha uma opção:*\n"
    "1. Ver Cardápio\n"
    "2. Fazer um Pedido\n"
    "3. Ver meu pedido\n"
    "4. Cancelar Atendimento"
)

MENU_MODIFICAR_PEDIDO_TEXT = (
    "\n*O que você gostaria de fazer?*\n"
    "1. Alterar a quantidade de um item\n"
    "2. Excluir um item do pedido\n"
    "3. Cancelar o pedido inteiro\n"
    "4. Voltar ao menu principal"
)

class ChatSession:
    def __init__(self, status):
        self.status = status

def start_gemini_chat(session_id):
    try:
        active_model_name = get_active_model_name()
        
        model = genai.GenerativeModel(active_model_name)

        chat = model.start_chat(history=[])
        
        gemini_chats[session_id] = chat
        logging.info(f"Chat com Gemini iniciado para {session_id} usando o modelo {active_model_name}.")
    except Exception as e:
        logging.error(f"Erro ao iniciar chat com Gemini para {session_id}: {e}")
        raise


def send_message_to_gemini(session_id, message):
    
    global model_request_count 
    try:
        if session_id not in gemini_chats:
            start_gemini_chat(session_id)

        model_request_count += 1
        logging.info(f"Contagem de requisições do Gemini: {model_request_count}")

        response = gemini_chats[session_id].send_message(message)
        logging.info(f"Mensagem enviada para Gemini. Resposta: {response.text}")
        return response.text
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para Gemini: {e}")
        raise

def formatar_historico(autor, mensagem):
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"[{agora}] {autor}: {mensagem}"

# --- Funções de Fluxo ---

def fluxo_tradicional(session_id, message):
    response = MENU_PRINCIPAL_TEXT
    chats[session_id] = ChatSession("tradicional")
    if session_id in historico_conversas:
        historico_conversas[session_id].append(formatar_historico("Bot", response))
    return response


def fluxo_inteligente(session_id, first_message):
    start_gemini_chat(session_id)
    chats[session_id] = ChatSession("inteligente")
    logging.info(f"Fluxo inteligente iniciado para {session_id} com a primeira mensagem: '{first_message}'")

    try:
        prompt = f"""<instruções>
                    Você é um atendente humano de uma pamonharia de delivery chamada Pamonha Express, em Uberlândia-MG. Essa pamonharia é fictícia e por isso não será feita nenhuma cobrança ou entrega de produtos, mas o atendimento deve simular um atendimento real. Responda como se estivesse anotando pedidos e lidando com dúvidas sobre o cardápio. Não se identifique como modelo de linguagem. Se perguntarem seu nome, diga que se chama Sara.
                    Aqui estão os itens do cardápio disponíveis com os preços:
                    - Pamonha doce: R$ 10,00
                    - Pamonha salgada: R$ 10,00
                    - Pamonha apimentada: R$ 12,00
                    - Curau clássico: R$ 8,00
                    - Milho cozido: R$ 6,00
                    - Bebidas:
                    - Suco: R$ 5,00
                    - Coca-Cola (lata): R$ 6,00
                    - Água: R$ 3,00
                    Geralmente a primeira mensagem do cliente será o nome dele, caso não seja, pergunte como ele gostaria de ser chamado. Se o cliente enviar a primeira mensagem já com o pedido, atenda o pedido normalmente.
                    Não pergunte endereços. Após o cliente confirmar o pedido, diga apenas que o pedido foi confirmado. Se o cliente perguntar sobre o status do pedido, diga que este atendimento é apenas para fins acadêmicos e que não há pedidos reais, mostre outras opções de cardapio ou pergunte se ele deseja fazer um novo pedido. Somente nesse caso fale sobre os fins acadêmicos. Sempre pergunte a quantidade de cada item após o cliente selecionar o que deseja. Pergunte também se ele deseja adicionar mais itens ou se já pode fechar o pedido. Sempre confirme as informações do pedido antes de dizer que está concluído. Para acompanhar pedidos, informe que o pedido está em preparação ou a caminho. Seja amigável e educado. Adapte seu tom ao humor do cliente (formal ou informal) e use emoticons de forma moderada. Trate endereços ou outras informações sensíveis apenas como dados logísticos para entrega e evite associá-los a interpretações adicionais. Peça desculpas ao cometer erros ou parecer insistente com alguma informação. NÃO se identifique como modelo de linguagem ou IA. Você deve parecer um atendente humano. Não minta. Não invente informações que você não tenha certeza. Use emoticons algumas vezes, mas NÃO exagere e nem use-os repetidamente. Você está respondendo no WhatsApp, um aplicativo de mensagens instantâneas no celular. Se receber mensagem com piadas ou que relacionem "cu" com curau, fique bravo, diga que é uma pamonharia de respeito, que está trabalhando e não aceita esse tipo de gracinha. Se o cliente insistir com essas brincadeiras ou piadas envolvendo "cu", diga que o atendimento está encerrado. Se receber uma mensagem com o texto "Mensagem de áudio recebida." diga que não consegue ouvir áudios no momento.
                    Se alguém perguntar a receita das pamonhas diga que é um segredo de família, mas que o sabor é incrível. Se insistirem, diga o básico sobre receitas de pamonha. Se perguntarem se tem queijo, diga que é opcional mas temos sim pamonhas com queijo e sem queijo. Se perguntarem sobre a pamonha apimentada, diga que pode escolher entre doce apimentada ou salgada apimentada.
                    Se perguntarem sobre o trabalho, diga que tem um link no rodapé do site falando sobre o projeto. Se perguntarem como fazer para testar um novo chat, diga que é necessário digitar "sair" para encerrar o atendimento.
                    </fim das instruções>
                    Pergunta do usuário: {first_message}"""
        
        response_text = send_message_to_gemini(session_id, prompt)
        historico_conversas[session_id].append(formatar_historico("Bot", response_text))
        return response_text
    except Exception as e:
        logging.error(f"Erro ao processar a primeira mensagem com Gemini: {e}")
        return "Um momento, por favor, estou com uma instabilidade no sistema."

def iniciar_fluxo_aleatorio(session_id, first_message):
    fluxo = random.choice([fluxo_tradicional, fluxo_inteligente])
    tipo_atendimento[session_id] = "tradicional" if fluxo == fluxo_tradicional else "inteligente"
    return fluxo(session_id, first_message)

def iniciar_questionario(session_id):
    """Inicia o questionário de avaliação com botões de estrela."""
    chats[session_id] = ChatSession("questionario_1")
        
    response_data = {
        "reply": "Obrigado por aceitar responder ao nosso questionário! 😊\n\n*Pergunta 1:* Em uma escala de 1 a 5, como você avalia sua satisfação nessa conversa?",
        "buttons": [
            {"label": "★", "value": "1"},
            {"label": "★★", "value": "2"},
            {"label": "★★★", "value": "3"},
            {"label": "★★★★", "value": "4"},
            {"label": "★★★★★", "value": "5"}
        ]
    }
    return response_data

def process_web_message(session_id, message_body):

    logging.info(f"Recebido de [session_id: {session_id}]: {message_body}")

    message_body = message_body.strip().lower()

    if session_id not in historico_conversas:
        historico_conversas[session_id] = []
        hora_inicio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        historico_conversas[session_id].append(f"--- Início da interação: {hora_inicio} ---")
    
    historico_conversas[session_id].append(formatar_historico("Usuário", message_body))

    # O comando universal "sair" é verificado primeiro e de forma isolada
    if message_body == "sair":
        hora_fim = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        historico_conversas[session_id].append(f"--- Fim da interação: {hora_fim} ---")
        response_data = {
            "reply": "Conversa encerrada. Se precisar de algo, estamos à disposição! 👋\n\nGostaria de responder a um breve questionário de avaliação?",
            "buttons": [{"label": "Sim", "value": "sim"}, {"label": "Não", "value": "nao"}]
        }
        chats[session_id] = ChatSession("avaliacao")
        historico_conversas[session_id].append(formatar_historico("Bot", response_data['reply']))
        tipo_chatbot = tipo_atendimento.get(session_id, "Desconhecido")
        salvar_historico_conversa(session_id, historico_conversas[session_id], tipo_chatbot)
        return response_data
    
    current_status = chats.get(session_id, ChatSession(None)).status

    if current_status is None:
        return iniciar_fluxo_aleatorio(session_id, message_body)

    elif current_status == "aguardando_interacao":
        return iniciar_fluxo_aleatorio(session_id, message_body)

    elif current_status == "tradicional":
        if session_id not in customer_data:
            customer_data[session_id] = {"pedido": [], "nome": None, "valor_total": 0.0}

        # Opção 1: Ver Cardápio
        if message_body in ["1", "um", "cardapio", "cardápio", "ver cardapio", "ver cardápio", "menu"]:
            response = ("📋 *Cardápio*\n\n"
                        "1 - Pamonha Doce: R$ 10,00\n2 - Pamonha Salgada: R$ 10,00\n"
                        "3 - Pamonha Apimentada: R$ 12,00\n4 - Curau Clássico: R$ 8,00\n"
                        "5 - Milho Cozido: R$ 6,00\n6 - Suco: R$ 5,00\n"
                        "7 - Coca-Cola Lata: R$ 6,00\n8 - Água Mineral: R$ 3,00\n\n"
                        "Para fazer um pedido, informe o número do item desejado.\n\n Ou digite *9* para voltar ao menu principal.")
            chats[session_id] = ChatSession("fazer_pedido")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return response

        # Opção 2: Fazer Pedido
        elif message_body in ["2", "dois", "pedido", "fazer pedido", "pedir", "fazer um pedido"]:
            response = "Por favor, informe o número do item que deseja pedir ou digite *9* para voltar ao menu principal e ver o cardápio."
            chats[session_id] = ChatSession("fazer_pedido")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return response

        # Opção 3: Ver meu pedido
        elif message_body in ["3", "três", "ver pedido", "meu pedido", "acompanhar", "status"]:
            if session_id in customer_data and customer_data[session_id]["pedido"]:
                pedido_atual = customer_data[session_id]["pedido"]
                valor_total = customer_data[session_id]["valor_total"]
                response_parts = ["*Seu pedido atual:*"]
                for item in pedido_atual:
                    response_parts.append(f"- {item['quantidade']}x {item['item']}")
                response_parts.append(f"\n*Valor Total: R$ {valor_total:.2f}*")
                pedido_formatado = "\n".join(response_parts)
                response = f"{pedido_formatado}\n\n{MENU_MODIFICAR_PEDIDO_TEXT}"
                chats[session_id] = ChatSession("modificar_pedido")
                historico_conversas[session_id].append(formatar_historico("Bot", response))
                return response
            else:
                aviso = "Você ainda não realizou um pedido."
                response = f"{aviso}\n\n{MENU_PRINCIPAL_TEXT}"
                historico_conversas[session_id].append(formatar_historico("Bot", response))
                return response

        elif message_body in ["4", "quatro", "cancelar", "cancelar atendimento"]:
            response_data = {
                "reply": "Conversa encerrada. Se precisar de algo, estamos à disposição! 👋\n\nGostaria de responder a um breve questionário de avaliação?",
                "buttons": [{"label": "Sim", "value": "sim"}, {"label": "Não", "value": "nao"}]
            }
            chats[session_id] = ChatSession("avaliacao")
            historico_conversas[session_id].append(formatar_historico("Bot", response_data['reply']))
            hora_fim = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            historico_conversas[session_id].append(f"--- Fim da interação: {hora_fim} ---")
            tipo_chatbot = tipo_atendimento.get(session_id, "Desconhecido")
            salvar_historico_conversa(session_id, historico_conversas[session_id], tipo_chatbot)
            return response_data
            
        # Nenhuma opção válida
        else:
            return fluxo_tradicional(session_id, message_body)

    elif current_status == "fazer_pedido":
        if message_body in ["9", "nove", "voltar"]:
            return fluxo_tradicional(session_id, message_body)
        try:
            item = int(message_body)
            cardapio = {1:("Pamonha Doce",10.00), 2:("Pamonha Salgada",10.00), 3:("Pamonha Apimentada",12.00), 4:("Curau Clássico",8.00), 5:("Milho Cozido",6.00), 6:("Suco",5.00), 7:("Coca-Cola Lata",6.00), 8:("Água Mineral",3.00)}
            if item in cardapio:
                response = f"Você escolheu {cardapio[item][0]} por R$ {cardapio[item][1]:.2f}.\nQuantas unidades deseja?"
                customer_data[session_id]["pedido"].append({"item": cardapio[item][0], "quantidade": 0, "preco": cardapio[item][1]})
                chats[session_id] = ChatSession("capturar_quantidade")
            else:
                response = "Não temos um item com esse número. Por favor, escolha um item válido do cardápio ou digite *9* para voltar ao menu principal."
        except ValueError:
            response = "Por favor, escolha um item válido do cardápio ou digite *9* para voltar ao menu principal."
        
        historico_conversas[session_id].append(formatar_historico("Bot", response))
        return response

    elif current_status == "capturar_quantidade":
        try:
            quantidade = int(message_body)
            if quantidade > 0:
                ultimo_item = customer_data[session_id]["pedido"][-1]
                total_item = ultimo_item["preco"] * quantidade
                customer_data[session_id]["valor_total"] += total_item
                customer_data[session_id]["pedido"][-1]["quantidade"] = quantidade
                
                response = {
                    "reply": f"Adicionado {quantidade}x {ultimo_item['item']} ao pedido.\nDeseja adicionar mais itens?",
                    "buttons": [{"label": "Sim", "value": "sim"}, {"label": "Não", "value": "nao"}]
                }
                chats[session_id] = ChatSession("adicionar_itens")
            else:
                response = "Quantidade inválida. Por favor, insira um número maior que zero."
        except ValueError:
            response = "Por favor, informe apenas a quantidade em números."

        response_text = response['reply'] if isinstance(response, dict) else response
        historico_conversas[session_id].append(formatar_historico("Bot", response_text))
        return response
    
    elif current_status == "adicionar_itens":
        if message_body in ["sim", "s", "quero", "claro", "pode", "pode ser"]:
            response = "Por favor, escolha o próximo item do cardápio."
            chats[session_id] = ChatSession("fazer_pedido")
        elif message_body in ["não", "nao", "n", "nao quero", "não quero", "finalizar", "fechar"]:
            response = "Qual o seu nome? Só para deixar registrado aqui no sistema."
            chats[session_id] = ChatSession("capturar_nome")
        else:

            response = {
                "reply": "Desculpa, não entendi. Deseja adicionar mais itens?",
                "buttons": [{"label": "Sim", "value": "sim"}, {"label": "Não", "value": "nao"}]
            }
        
        response_text = response['reply'] if isinstance(response, dict) else response
        historico_conversas[session_id].append(formatar_historico("Bot", response_text))
        return response

    elif current_status == "capturar_nome":
        customer_data[session_id]["nome"] = message_body.title()
        aviso = f"Obrigado, {customer_data[session_id]['nome']}! Seu pedido foi recebido com sucesso! Obrigado por escolher a Pamonha Express! 😊"
        response = f"{aviso}\n\n{MENU_PRINCIPAL_TEXT}"
        chats[session_id] = ChatSession("tradicional")
        
        historico_conversas[session_id].append(formatar_historico("Bot", response))
        return response

    elif current_status == "consultar_pedido":
        response = "Desculpe, ainda não implementamos a consulta de pedidos."
        chats[session_id] = ChatSession("tradicional")
        historico_conversas[session_id].append(formatar_historico("Bot", response))
        return response

    elif current_status == "modificar_pedido":
        if message_body in ["1", "um", "alterar", "quantidade", "alterar quantidade"]:
            pedido_atual = customer_data[session_id]["pedido"]
            response_parts = ["*Qual item você deseja alterar a quantidade?*"]
            for i, item in enumerate(pedido_atual, start=1):
                response_parts.append(f"{i}. {item['quantidade']}x {item['item']}")
            response = "\n".join(response_parts)
            chats[session_id] = ChatSession("alterar_quantidade_item")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return response
        elif message_body in ["2", "dois", "excluir", "remover", "excluir item"]:
            pedido_atual = customer_data[session_id]["pedido"]
            response_parts = ["*Qual item você deseja excluir do pedido?*"]
            for i, item in enumerate(pedido_atual, start=1):
                response_parts.append(f"{i}. {item['item']}")
            response = "\n".join(response_parts)
            chats[session_id] = ChatSession("excluir_item")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return response
        elif message_body in ["3", "três", "cancelar", "cancelar tudo", "cancelar pedido"]:
            customer_data[session_id]["pedido"] = []
            customer_data[session_id]["valor_total"] = 0.0
            response = "Seu pedido foi cancelado com sucesso."
            chats[session_id] = ChatSession("tradicional")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return f"{response}\n\n{MENU_PRINCIPAL_TEXT}"
        elif message_body in ["4", "quatro", "voltar", "menu principal"]:
            return fluxo_tradicional(session_id, message_body)
        else:
            return f"Opção inválida.\n{MENU_MODIFICAR_PEDIDO_TEXT}"

    elif current_status == "excluir_item":
        try:
            item_index = int(message_body) - 1
            pedido_atual = customer_data[session_id]["pedido"]
            if 0 <= item_index < len(pedido_atual):
                item_removido = pedido_atual.pop(item_index)
                novo_total = sum(item['preco'] * item['quantidade'] for item in pedido_atual)
                customer_data[session_id]["valor_total"] = novo_total
                response = f"Item '{item_removido['item']}' removido do seu pedido."
                if not pedido_atual:
                    chats[session_id] = ChatSession("tradicional")
                    historico_conversas[session_id].append(formatar_historico("Bot", response))
                    return f"{response}\nSeu pedido agora está vazio.\n\n{MENU_PRINCIPAL_TEXT}"
                else:
                    chats[session_id] = ChatSession("modificar_pedido")
                    historico_conversas[session_id].append(formatar_historico("Bot", response))
                    return f"{response}{MENU_MODIFICAR_PEDIDO_TEXT}"
            else:
                return "Número inválido. Por favor, escolha um número da lista."
        except ValueError:
            return "Por favor, informe um número válido."
            
    elif current_status == "alterar_quantidade_item":
        try:
            item_index = int(message_body) - 1
            pedido_atual = customer_data[session_id]["pedido"]
            if 0 <= item_index < len(pedido_atual):
                customer_data[session_id]["item_para_alterar"] = item_index
                item_nome = pedido_atual[item_index]["item"]
                chats[session_id] = ChatSession("alterar_quantidade_valor")
                response = f"Qual a nova quantidade para *{item_nome}*?"
                
                historico_conversas[session_id].append(formatar_historico("Bot", response))
                return response
            else:
                response = "Número inválido. Por favor, escolha um número da lista."
        except ValueError:
            response = "Por favor, informe um número válido."
        
        # Log e return para os casos de erro
        historico_conversas[session_id].append(formatar_historico("Bot", response))
        return response

    elif current_status == "alterar_quantidade_valor":
        try:
            nova_quantidade = int(message_body)
            item_index = customer_data[session_id]["item_para_alterar"]
            if nova_quantidade > 0:
                customer_data[session_id]["pedido"][item_index]["quantidade"] = nova_quantidade
                novo_total = sum(item['preco'] * item['quantidade'] for item in customer_data[session_id]["pedido"])
                customer_data[session_id]["valor_total"] = novo_total
                response = "Quantidade alterada com sucesso!"
                chats[session_id] = ChatSession("modificar_pedido")
                pedido_atual = customer_data[session_id]["pedido"]
                response_parts = ["*Seu pedido atual:*"]
                for item in pedido_atual:
                    response_parts.append(f"- {item['quantidade']}x {item['item']}")
                response_parts.append(f"\n*Valor Total: R$ {novo_total:.2f}*")
                pedido_formatado = "\n".join(response_parts)
                historico_conversas[session_id].append(formatar_historico("Bot", response))
                return f"{response}\n\n{pedido_formatado}\n{MENU_MODIFICAR_PEDIDO_TEXT}"
            else:
                item_removido = customer_data[session_id]["pedido"].pop(item_index)
                novo_total = sum(item['preco'] * item['quantidade'] for item in customer_data[session_id]["pedido"])
                customer_data[session_id]["valor_total"] = novo_total
                chats[session_id] = ChatSession("modificar_pedido")
                return f"Item '{item_removido['item']}' removido do seu pedido.{MENU_MODIFICAR_PEDIDO_TEXT}"
        except ValueError:
            return "Por favor, informe um número válido para a quantidade."

    elif current_status == "avaliacao":
        # Caminho para iniciar o questionário
        if message_body in ["sim", "s", "quero", "claro", "pode", "pode ser"]:
            return iniciar_questionario(session_id)
        
        # Caminho para NÃO responder o questionário
        elif message_body in ["não", "nao", "n", "nao quero", "não quero"]:
            response = "Tudo bem! Agradecemos pelo seu tempo. Até logo! 👋\n\n Para iniciar um novo atendimento, envie uma nova mensagem."
            chats[session_id] = ChatSession("aguardando_interacao")
            historico_conversas[session_id].append(formatar_historico("Bot", response))
            return response
        
        # Caminho para resposta inválida
        else:
            response_data = {
                "reply": "Desculpe, não entendi. Por favor, responda com 'Sim' ou 'Não'.",
                "buttons": [
                    {"label": "Sim, quero responder", "value": "sim"},
                    {"label": "Não, obrigado(a)", "value": "nao"}
                ]
            }            
            return response_data

    elif current_status.startswith("questionario"):
        if current_status == "questionario_1":
            respostas_questionario[session_id] = {"Pergunta 1": message_body}
            chats[session_id] = ChatSession("questionario_2")
            return {
                "reply": "Pergunta 2: Você conseguiu realizar o que desejava nesta conversa (ex: ver o cardápio, fazer um pedido, etc.)?",
                "buttons": [
                    {"label": "Sim, consegui", "value": "Sim, consegui"},
                    {"label": "Parcialmente", "value": "Parcialmente"},
                    {"label": "Não consegui", "value": "Não consegui"}
                ]
            }
        elif current_status == "questionario_2":
            respostas_questionario[session_id]["Pergunta 2"] = message_body
            chats[session_id] = ChatSession("questionario_3")

            return {
                "reply": "Pergunta 3: Em um cenário real, você iria preferir utilizar este chatbot ou um atendimento humano?",
                "buttons": [
                    {"label": "Usaria este chatbot ou um semelhante", "value": "Usaria o chatbot"},
                    {"label": "Ainda prefiro atendimento humano", "value": "Prefiro humano"}
                ]
            }
        elif current_status == "questionario_3":
            respostas_questionario[session_id]["Pergunta 3"] = message_body
            chats[session_id] = ChatSession("questionario_4")
            return "Para finalizar, você tem alguma sugestão, crítica ou feedback sobre sua experiência?"
        elif current_status == "questionario_4":
            respostas_questionario[session_id]["Pergunta 4 (Feedback)"] = message_body
            salvar_respostas_questionario(session_id)
            
            chats[session_id] = ChatSession("aguardando_interacao")
            
            return "Obrigado por suas respostas e pelo seu feedback! Sua opinião é muito importante. Até logo! 👋\n\n Para iniciar um novo atendimento, envie uma nova mensagem."
    
    elif current_status == "inteligente":
        try:
            response_text = send_message_to_gemini(session_id, message_body)
            historico_conversas[session_id].append(formatar_historico("Bot", response_text))
            return response_text
        except Exception as e:
            logging.error(f"Erro ao processar mensagem com Gemini: {e}")
            return "Um momento, por favor, estou com uma instabilidade no sistema."
    return "Desculpe, não entendi o que você quis dizer."

def salvar_historico_conversa(session_id, historico, tipo_chatbot):
    try:        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
        log_conversations_dir = os.path.join(project_root, 'logs', 'conversations')
        os.makedirs(log_conversations_dir, exist_ok=True)
        
        nome_arquivo = f"{session_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        caminho_arquivo_conversa = os.path.join(log_conversations_dir, nome_arquivo)

        with open(caminho_arquivo_conversa, "w", encoding="utf-8") as arquivo:
            arquivo.write(f"Tipo de Atendimento: {tipo_chatbot}\n\n")
            arquivo.write("\n".join(historico))
        logging.info(f"Histórico da conversa salvo em: {caminho_arquivo_conversa}")
        
        log_main_dir = os.path.join(project_root, 'logs')
        log_list_path = os.path.join(log_main_dir, "log-list.json")

        log_list = []
        if os.path.exists(log_list_path):
            with open(log_list_path, "r", encoding="utf-8") as f:
                log_list = json.load(f)

        log_list.insert(0, nome_arquivo)

        with open(log_list_path, "w", encoding="utf-8") as f:
            json.dump(log_list, f, indent=2, ensure_ascii=False)
        logging.info("Arquivo de índice 'log-list.json' atualizado com sucesso.")

    except Exception as e:
        logging.error(f"Erro ao salvar histórico ou atualizar índice: {e}")
        
def salvar_respostas_questionario(session_id):
    try:        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        diretorio_logs = os.path.join(project_root, "logs", "questionarios")
        os.makedirs(diretorio_logs, exist_ok=True)
        
        nome_arquivo = f"questionario_{session_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        caminho_arquivo = os.path.join(diretorio_logs, nome_arquivo)
        tipo_chatbot = tipo_atendimento.get(session_id, "Desconhecido")

        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write(f"Tipo de Atendimento: {tipo_chatbot}\n")
            arquivo.write("Respostas do Questionário:\n\n")
            perguntas = [
                "Pergunta 1: Em uma escala de 1 a 5, como você avalia sua satisfação nessa conversa?",
                "Pergunta 2: Você conseguiu realizar o que desejava nesta conversa (ex: ver o cardápio, fazer um pedido, etc.)?",
                "Pergunta 3: Em um cenário real, você iria preferir utilizar este chatbot ou um atendimento humano?",
                "Pergunta 4 (Feedback): Para finalizar, você tem alguma sugestão, crítica ou feedback para nos dar sobre sua experiência?"
            ]
            for i, pergunta in enumerate(perguntas, start=1):
                key = f"Pergunta {i}" if i <= 3 else "Pergunta 4 (Feedback)"
                resposta = respostas_questionario[session_id].get(key, "Não respondida")
                arquivo.write(f"{pergunta}\nResposta: {resposta}\n\n")

        logging.info(f"Respostas do questionário salvas em: {caminho_arquivo}")
        
        log_main_dir = os.path.join(project_root, 'logs')
        log_list_path = os.path.join(log_main_dir, "questionario-list.json")

        log_list = []

        if os.path.exists(log_list_path):
            with open(log_list_path, "r", encoding="utf-8") as f:
                log_list = json.load(f)
        
        log_list.insert(0, nome_arquivo)

        # Salva a lista atualizada de volta no arquivo JSON
        with open(log_list_path, "w", encoding="utf-8") as f:
            json.dump(log_list, f, indent=2, ensure_ascii=False)
        
        logging.info("Arquivo de índice 'questionario-list.json' atualizado.")
        
        if session_id in respostas_questionario: del respostas_questionario[session_id]
        if session_id in tipo_atendimento: del tipo_atendimento[session_id]
        if session_id in historico_conversas: del historico_conversas[session_id]
        
        chats[session_id] = ChatSession("aguardando_interacao")

    except Exception as e:
        logging.error(f"Erro ao salvar respostas do questionário ou atualizar índice: {e}")