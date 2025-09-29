import importlib
import os
import socket
import time
import webbrowser

import uvicorn


def port_open(host, port) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def load_app(dotted: str):
    mod_name, obj_name = dotted.split(":", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, obj_name)


def main():
    host = os.environ.get("FASTFORM_HOST", "127.0.0.1")
    port = int(os.environ.get("FASTFORM_PORT", "8000"))
    app_path = os.environ.get("FASTFORM_APP", "fastform.api.app:app")
    app = load_app(app_path)

    cfg = uvicorn.Config(app, host=host, port=port, log_level="info", workers=1, reload=False)
    server = uvicorn.Server(cfg)

    def open_when_ready():
        for _ in range(100):
            if port_open(host, port):
                webbrowser.open(f"http://{host}:{port}/v1/health")
                break
            time.sleep(0.1)

    import threading

    threading.Thread(target=open_when_ready, daemon=True).start()
    server.run()


if __name__ == "__main__":
    main()
