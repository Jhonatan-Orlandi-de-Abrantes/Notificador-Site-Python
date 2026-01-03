# app.py -- servidor Flask (em processo filho) + notifier (no processo principal)
import multiprocessing
import time
import sys
from winotify import Notification, audio

def start_flask(queue):
    # Import interno para evitar problemas de multiprocess on Windows
    from flask import Flask, request, jsonify
    from flask_cors import CORS

    app = Flask(__name__, static_folder=None)
    CORS(app)  # libera CORS para testes locais (file:// or http origins)

    @app.route("/notify", methods=["POST"])
    def notify():
        try:
            data = request.get_json(force=True)
            title = data.get("title", "Notificação")
            message = data.get("message", "Mensagem do site")
            # coloca na fila compartilhada
            queue.put((title, message))
            print(f"[Flask] Enfileirado: {title} — {message}", flush=True)
            return jsonify({"status": "enqueued"}), 200
        except Exception as e:
            print("[Flask] Erro ao processar /notify:", e, flush=True)
            return jsonify({"status": "error", "error": str(e)}), 500

    # Rodar servidor (sem reloader)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def show_notification(title: str, message: str, app_id: str = "TesteNotificacaoPython"):
    try:
        toast = Notification(
            app_id=app_id,
            title=title,
            msg=message,
            duration="short"
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()  # <- chamada essencial para exibir a notificação
        print(f"[Notifier] NOTIFICADO: {title} — {message}", flush=True)
    except Exception as e:
        print("[Notifier] Erro ao mostrar toast:", e, flush=True)

def notification_loop(queue):
    print("[Notifier] Iniciado — aguardando notificações (Ctrl+C para sair).", flush=True)
    while True:
        try:
            title, message = queue.get()  # bloqueante — evita busy-loop
            show_notification(title, message)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("[Notifier] Erro no loop:", e, flush=True)

if __name__ == "__main__":
    # Necessário para multiprocessing no Windows
    q = multiprocessing.Queue()

    flask_proc = multiprocessing.Process(target=start_flask, args=(q,), daemon=True)
    flask_proc.start()
    print(f"[Main] Flask iniciado (PID {flask_proc.pid}). Endpoint: http://127.0.0.1:5000/notify", flush=True)

    try:
        notification_loop(q)
    except KeyboardInterrupt:
        print("\n[Main] Finalizando...", flush=True)
        try:
            flask_proc.terminate()
            flask_proc.join(timeout=2)
        except Exception:
            pass
        sys.exit(0)
