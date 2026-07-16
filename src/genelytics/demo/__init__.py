"""Flask demo app wrapping AnalyticsEngine."""

from __future__ import annotations

import os
from pathlib import Path

from genelytics.engine import AnalyticsEngine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATE_DIR = _REPO_ROOT / "templates"


def create_app(engine: AnalyticsEngine | None = None):
    try:
        from flask import Flask, jsonify, request, send_from_directory
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Flask is required for the demo. Install with: pip install 'genelytics[demo]'"
        ) from exc

    app = Flask(__name__, template_folder=str(_TEMPLATE_DIR))
    app.config["ENGINE"] = engine or AnalyticsEngine.from_env()

    @app.route("/")
    def index():
        return send_from_directory(str(_TEMPLATE_DIR), "index.html")

    @app.route("/user_prompt.html")
    def user_prompt_page():
        return send_from_directory(str(_TEMPLATE_DIR), "user_prompt.html")

    @app.route("/set_db_config", methods=["POST"])
    def set_db_config():
        eng: AnalyticsEngine = app.config["ENGINE"]
        try:
            data = request.get_json(force=True, silent=True) or {}
            db_config = data.get("db_config") or data
            if not db_config:
                raise ValueError("Missing 'db_config' data in request body.")
            eng.connect(**db_config)
            tables = eng.list_tables()
            return jsonify(
                {
                    "message": "Database configuration set successfully.",
                    "tables": tables,
                }
            )
        except (ValueError, KeyError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": str(e)}), 500

    @app.route("/user_prompt", methods=["POST"])
    def process_input():
        eng: AnalyticsEngine = app.config["ENGINE"]
        if not eng.is_connected:
            return jsonify({"error": "Database connection not established"}), 500

        payload = request.get_json(force=True, silent=True) or {}
        user_prompt = payload.get("user_prompt") or payload.get("question")
        session_id = payload.get("session_id", "default")

        if not user_prompt:
            return jsonify({"error": "Invalid input"}), 400

        result = eng.ask(user_prompt, session_id=session_id)
        display = result.answer or result.error or ""
        body = {
            "answer": result.answer,
            "sql": result.sql,
            "rows": result.data,
            "columns": result.columns,
            "error": result.error,
            "intent": result.intent,
            "truncated": result.truncated,
            # templates/legacy clients
            "result": display,
        }
        status = 200 if not result.error else 200  # still return payload for chat UI
        return jsonify(body), status

    return app


def main() -> None:
    os.environ.setdefault("GENELYTICS_ENV", "local")
    app = create_app()
    host = os.environ.get("GENELYTICS_DEMO_HOST", "0.0.0.0")
    port = int(os.environ.get("GENELYTICS_DEMO_PORT", "5000"))
    debug = os.environ.get("GENELYTICS_DEMO_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
