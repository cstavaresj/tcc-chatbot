import logging
from flask import Blueprint, request, jsonify
from .utils.whatsapp_utils import process_web_message

webhook_blueprint = Blueprint("webhook", __name__)

@webhook_blueprint.route("/chat", methods=["POST", "OPTIONS"])
def handle_chat():    
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        #response.headers.add("Access-Control-Allow-Origin", "https://DOMINIO-FRONT-END")
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    # Lógica para as requisições POST
    try:
        data = request.get_json()
        session_id = data.get("sessionId")
        user_message = data.get("message")

        if not session_id or not user_message:
            return jsonify({"status": "error", "message": "sessionId e message são obrigatórios"}), 400
        
        response_data = process_web_message(session_id, user_message)

        # Verifica se a resposta da sua lógica já é um dicionário (ex: com botões)
        if isinstance(response_data, dict):
            # Se for, apenas o converte para JSON
            return jsonify(response_data)
        else:
            # Se for texto simples, envolve no formato padrão {"reply": "..."}
            return jsonify({"reply": response_data})

    except Exception as e:
        logging.error(f"Erro ao processar a mensagem do chat: {e}")
        return jsonify({"status": "error", "message": "Ocorreu um erro interno no servidor"}), 500