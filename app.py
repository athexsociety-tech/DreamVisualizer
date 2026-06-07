"""
Dream Visualizer AI - Flask Backend
Production-grade REST API
"""

import logging
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS

from ai_engine import DreamAnalyzer
from analytics import AnalyticsEngine
from database import (
    create_database,
    delete_dream,
    get_all_dreams,
    get_dream,
    get_statistics,
    save_dream,
)
from image_generator import DreamImageGenerator

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dream_visualizer")

# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialise subsystems
    create_database()
    analyzer = DreamAnalyzer()
    img_gen = DreamImageGenerator()
    analytics = AnalyticsEngine()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def success(data: dict | list, status: int = 200):
        return jsonify({"success": True, "data": data}), status

    def error(message: str, status: int = 400):
        return jsonify({"success": False, "error": message}), status

    def require_json(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return error("Content-Type must be application/json")
            return f(*args, **kwargs)
        return wrapper

    # ── Health ────────────────────────────────────────────────────────────────

    @app.route("/api/health", methods=["GET"])
    def health():
        return success({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

    # ── Dream Analysis ────────────────────────────────────────────────────────

    @app.route("/api/analyze-dream", methods=["POST"])
    @require_json
    def analyze_dream():
        body = request.get_json()
        dream_text: str = (body.get("dream_text") or "").strip()
        title: str = (body.get("title") or "Untitled Dream").strip()

        if not dream_text:
            return error("dream_text is required")
        if len(dream_text) < 10:
            return error("dream_text is too short (min 10 characters)")
        if len(dream_text) > 5000:
            return error("dream_text is too long (max 5000 characters)")

        logger.info("Analysing dream: %s chars", len(dream_text))
        try:
            analysis = analyzer.generate_ai_response(dream_text)
        except Exception as exc:
            logger.exception("Analysis failed")
            return error(f"Analysis failed: {exc}", 500)

        return success({
            "title": title,
            "dream_text": dream_text,
            **analysis,
        })

    # ── Save Dream ────────────────────────────────────────────────────────────

    @app.route("/api/save-dream", methods=["POST"])
    @require_json
    def api_save_dream():
        body = request.get_json()
        required = ["title", "dream_text", "mood", "emotion_score",
                    "summary", "interpretation", "symbols", "dream_score"]
        missing = [k for k in required if k not in body]
        if missing:
            return error(f"Missing fields: {', '.join(missing)}")

        try:
            dream_id = save_dream(
                title=body["title"],
                dream_text=body["dream_text"],
                mood=body["mood"],
                emotion_score=float(body["emotion_score"]),
                summary=body["summary"],
                interpretation=body["interpretation"],
                symbols=body["symbols"],           # list → stored as JSON string
                dream_score=float(body["dream_score"]),
                image_url=body.get("image_url", ""),
            )
        except Exception as exc:
            logger.exception("Save failed")
            return error(f"Could not save dream: {exc}", 500)

        return success({"id": dream_id, "message": "Dream saved successfully"}, 201)

    # ── List Dreams ───────────────────────────────────────────────────────────

    @app.route("/api/dreams", methods=["GET"])
    def list_dreams():
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
        try:
            dreams = get_all_dreams(limit=limit, offset=offset)
        except Exception as exc:
            logger.exception("Fetch dreams failed")
            return error(f"Could not fetch dreams: {exc}", 500)
        return success({"dreams": dreams, "count": len(dreams)})

    # ── Single Dream ──────────────────────────────────────────────────────────

    @app.route("/api/dream/<dream_id>", methods=["GET"])
    def get_single_dream(dream_id: str):
        dream = get_dream(dream_id)
        if dream is None:
            return error("Dream not found", 404)
        return success(dream)

    # ── Delete Dream ──────────────────────────────────────────────────────────

    @app.route("/api/dream/<dream_id>", methods=["DELETE"])
    def api_delete_dream(dream_id: str):
        dream = get_dream(dream_id)
        if dream is None:
            return error("Dream not found", 404)
        try:
            delete_dream(dream_id)
        except Exception as exc:
            logger.exception("Delete failed")
            return error(f"Could not delete dream: {exc}", 500)
        return success({"message": "Dream deleted", "id": dream_id})

    # ── Stats ─────────────────────────────────────────────────────────────────

    @app.route("/api/stats", methods=["GET"])
    def stats():
        try:
            raw = get_statistics()
            enriched = analytics.build_dashboard(raw)
        except Exception as exc:
            logger.exception("Stats failed")
            return error(f"Could not compute stats: {exc}", 500)
        return success(enriched)

    # ── Image Generation ──────────────────────────────────────────────────────

    @app.route("/api/generate-image", methods=["POST"])
    @require_json
    def generate_image():
        body = request.get_json()
        dream_text: str = (body.get("dream_text") or "").strip()
        mood: str = body.get("mood", "mystery")

        if not dream_text:
            return error("dream_text is required")

        try:
            prompt = img_gen.generate_dream_prompt(dream_text, mood)
            # In production swap this placeholder URL for a real image API call.
            image_url = img_gen.get_placeholder_url(prompt)
        except Exception as exc:
            logger.exception("Image generation failed")
            return error(f"Image generation failed: {exc}", 500)

        return success({"prompt": prompt, "image_url": image_url})

    # ── Error handlers ────────────────────────────────────────────────────────

    @app.errorhandler(404)
    def not_found(_e):
        return error("Endpoint not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error("Method not allowed", 405)

    @app.errorhandler(413)
    def too_large(_e):
        return error("Payload too large (max 1 MB)", 413)

    @app.errorhandler(500)
    def internal(_e):
        logger.exception("Unhandled 500")
        return error("Internal server error", 500)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting Dream Visualizer on port %s  debug=%s", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
