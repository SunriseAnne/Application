# -*- coding: utf-8 -*-
"""Lansator desktop: pornește aplicația Streamlit și o deschide într-o fereastră proprie (pywebview)."""
import os, socket, subprocess, sys, time, webbrowser

PORT = 8765


def main():
    app = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", app, "--server.headless", "true",
                            "--server.port", str(PORT), "--browser.gatherUsageStats", "false"])
    for _ in range(60):
        try:
            socket.create_connection(("localhost", PORT), 1).close()
            break
        except OSError:
            time.sleep(0.5)
    url = f"http://localhost:{PORT}"
    try:
        import webview
        webview.create_window("Algebră Booleană", url, width=1000, height=850)
        webview.start()
    except ImportError:
        webbrowser.open(url)
        srv.wait()
    finally:
        srv.terminate()


if __name__ == "__main__":
    main()
