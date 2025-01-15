import os
import socket
import paramiko
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Inicializar Flask e SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Lista de saudações e respostas automáticas
saudacoes = {
    "olá": "Olá! Como posso te ajudar hoje?",
    "oi": "Oi! Em que posso te ajudar?",
    "bom dia": "Bom dia! Como posso ajudar?",
    "boa tarde": "Boa tarde! Espero que esteja tudo bem!",
    "boa noite": "Boa noite! Pronto para te ajudar!"
}

# Função para executar comandos de rede com tratamento de erros e timeout
def execute_command(device_ip, command):
    try:
        username = "usuario"  #usuario para acessar os equipamentos
        password = "senha"    #senha para acessar os equipamentos

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(device_ip, username=username, password=password, timeout=10)

        # Executar comando com timeout para evitar bloqueio
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)
        output = stdout.read().decode()

        ssh.close()
        return output if output else "Comando executado, mas sem saída relevante."

    except paramiko.AuthenticationException:
        return f"Erro: Falha na autenticação ao dispositivo {device_ip}. Verifique as credenciais."
    except paramiko.SSHException as e:
        return f"Erro: Problema de conexão SSH ao dispositivo {device_ip}: {str(e)}"
    except socket.timeout:
        return f"Erro: Tempo de conexão esgotado ao tentar acessar o dispositivo {device_ip}. Verifique a rede."
    except Exception as e:
        return f"Erro inesperado ao conectar ao dispositivo {device_ip}: {str(e)}"

# Função para verificar se é um comando de rede
def is_network_command(msg):
    network_keywords = ["status das interfaces", "descrição das interfaces", "versão do sistema"]
    for keyword in network_keywords:
        if keyword in msg.lower():
            return True
    return False

# Função para verificar se é uma saudação
def is_saudacao(msg):
    for saudacao in saudacoes:
        if saudacao in msg.lower():
            return saudacoes[saudacao]
    return None

# Rota principal
@app.route('/')
def index():
    return render_template('chat.html')

# Evento de mensagem recebida
@socketio.on('message')
def handle_message(msg):
    # Verificar se é uma saudação
    saudacao_resposta = is_saudacao(msg)
    if saudacao_resposta:
        response = saudacao_resposta
    elif is_network_command(msg):
        words = msg.split()
        device_ip = words[-1]
        if "status" in msg.lower():
            command_type = "display interface brief"
        elif "descrição" in msg.lower():
            command_type = "display interface description"
        else:
            command_type = "display version"

        response = execute_command(device_ip, command_type)
    else:
        response = "Comando não reconhecido. Tente comandos como: 'status das interfaces <IP>'."

    emit('response', response)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
