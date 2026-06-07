"""
Dream Visualizer AI - AI Engine
Rule-based + statistical dream analysis. Drop-in for an LLM backend.
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("dream_visualizer.ai_engine")

# ── Emotion lexicons ──────────────────────────────────────────────────────────

EMOTION_LEXICON: dict[str, list[str]] = {
    "Happy": [
        "happy", "joy", "laugh", "smile", "cheerful", "bright", "sunny",
        "wonderful", "bliss", "celebrate", "dance", "fun", "delight", "gleam",
        "glow", "merry", "paradise", "rainbow", "treasure",
    ],
    "Fear": [
        "fear", "scared", "terror", "horror", "monster", "dark", "shadow",
        "scream", "trapped", "chase", "panic", "nightmare", "ghost", "haunt",
        "dread", "shiver", "creep", "abyss", "shriek", "flee",
    ],
    "Adventure": [
        "fly", "climb", "explore", "journey", "mountain", "quest", "discover",
        "travel", "expedition", "run", "swim", "dive", "forest", "treasure",
        "map", "dragon", "hero", "sword", "brave", "adventure",
    ],
    "Mystery": [
        "mystery", "strange", "unknown", "portal", "door", "fog", "secret",
        "ancient", "symbol", "code", "hidden", "labyrinth", "figure", "sign",
        "whisper", "clue", "vision", "cryptic", "omen",
    ],
    "Love": [
        "love", "romance", "heart", "kiss", "embrace", "wedding", "tender",
        "together", "bond", "passion", "warm", "care", "affection", "soulmate",
        "cherish", "adore", "longing", "reunion",
    ],
    "Anxiety": [
        "anxiety", "worry", "late", "lost", "exam", "fail", "fall", "stuck",
        "crowd", "pressure", "stress", "overwhelm", "nervous", "tense",
        "unprepared", "judge", "watch", "expose",
    ],
    "Excitement": [
        "exciting", "thrilling", "rush", "speed", "power", "energy", "electric",
        "awesome", "amazing", "incredible", "fantastic", "soar", "burst",
        "surge", "ignite", "blast", "spectacular",
    ],
    "Sadness": [
        "sad", "cry", "tears", "lonely", "loss", "grief", "miss", "empty",
        "hurt", "pain", "sorrow", "mourn", "regret", "fade", "broken",
        "silent", "dark", "grey", "rain", "goodbye",
    ],
}

# ── Symbol lexicon ────────────────────────────────────────────────────────────

SYMBOL_MEANINGS: dict[str, str] = {
    "water":     "emotions and the unconscious",
    "fire":      "transformation and passion",
    "flying":    "freedom and ambition",
    "falling":   "loss of control or anxiety",
    "house":     "the self and inner world",
    "door":      "new opportunities or transitions",
    "snake":     "hidden fears or wisdom",
    "tree":      "growth and stability",
    "mountain":  "challenges and achievement",
    "mirror":    "self-reflection and identity",
    "bridge":    "transition between life phases",
    "forest":    "the unconscious mind",
    "road":      "life's journey and direction",
    "light":     "insight, hope, or revelation",
    "darkness":  "the unknown or hidden aspects",
    "clock":     "time pressure or mortality",
    "ocean":     "vast emotions or the unconscious",
    "moon":      "intuition and cyclical change",
    "sun":       "vitality, clarity, and success",
    "storm":     "emotional turmoil or conflict",
    "child":     "innocence or a new beginning",
    "death":     "transformation, ending, or change",
    "flight":    "ambition or desire to escape",
    "chase":     "avoidance or confronting fears",
    "dragon":    "inner power or overwhelming force",
    "city":      "social world and ambition",
    "animal":    "instincts and natural impulses",
    "school":    "learning, evaluation, or self-doubt",
    "music":     "emotional expression and harmony",
    "gold":      "value, achievement, or ego",
}

# ── Interpretation templates ──────────────────────────────────────────────────

INTERPRETATION_TEMPLATES: dict[str, list[str]] = {
    "Happy": [
        "This dream reflects a period of emotional fulfilment and contentment. Your subconscious is processing joy and positive energy, suggesting alignment between your waking desires and inner values.",
        "The happiness in this dream signals that your mind is in a state of harmony. You may be experiencing, or yearning for, a time of peace and satisfaction in your waking life.",
    ],
    "Fear": [
        "Fear-based dreams often represent unresolved anxieties or suppressed emotions. Your subconscious is using vivid imagery to force a confrontation with something you've been avoiding.",
        "This dream may reflect deep-seated concerns about vulnerability or loss of control. Consider what in your waking life feels threatening or uncertain.",
    ],
    "Adventure": [
        "An adventure-themed dream reveals a deep desire for growth, exploration, and breaking free from routine. Your subconscious is energised and ready to face new challenges.",
        "This dream suggests you are in—or are seeking—a period of dynamic personal growth. The adventurous imagery represents your inner drive to push boundaries.",
    ],
    "Mystery": [
        "Mystery dreams indicate that your subconscious is grappling with unanswered questions or hidden truths. Something significant lies just beneath the surface of your awareness.",
        "This dream is an invitation to explore the unknown parts of yourself. The cryptic symbols suggest that important self-knowledge is waiting to be discovered.",
    ],
    "Love": [
        "Love-filled dreams reflect the heart's deepest desires for connection and belonging. Your subconscious is processing relationships—past, present, or idealised.",
        "This dream suggests a deep need for emotional intimacy and meaningful bonds. It may also reflect love for yourself or a longing for reunion with someone cherished.",
    ],
    "Anxiety": [
        "Anxiety dreams are the mind's rehearsal space for real-world stressors. They highlight areas where you feel unprepared, judged, or under pressure.",
        "This dream is a signal that your nervous system is processing stress. Identifying the source of that pressure in your waking life may bring significant relief.",
    ],
    "Excitement": [
        "Excitement in a dream mirrors your waking enthusiasm and readiness for change. Your subconscious is charged with anticipation for something on the horizon.",
        "This dream reflects a surge of creative and motivational energy. You are likely on the cusp of a breakthrough or an exciting new chapter.",
    ],
    "Sadness": [
        "Sad dreams are the mind's way of processing grief, loss, or unfulfilled longing. Your subconscious is doing important emotional work—allowing feelings to surface that may be suppressed when awake.",
        "This dream suggests unresolved sadness or a sense of something missing. Your inner world is asking for acknowledgment and gentle self-compassion.",
    ],
}


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    emotion: str
    confidence: float
    summary: str
    interpretation: str
    symbols: list[dict[str, str]]
    dream_score: float
    recurring_patterns: list[str] = field(default_factory=list)


# ── Engine ────────────────────────────────────────────────────────────────────

class DreamAnalyzer:
    """
    Offline, deterministic dream analysis engine.
    Replace or augment any method with LLM calls for richer output.
    """

    # ── Public API ──────────────────────────────────────────────────────────

    def generate_ai_response(self, dream_text: str) -> dict[str, Any]:
        """
        Master method: analyse a dream and return a serialisable dict.
        """
        logger.info("Running full analysis on %d-char text", len(dream_text))
        emotion, confidence = self.analyze_emotion(dream_text)
        symbols             = self.extract_symbols(dream_text)
        summary             = self.generate_summary(dream_text, emotion)
        interpretation      = self.generate_interpretation(dream_text, emotion, symbols)
        dream_score         = self.calculate_dream_score(dream_text, emotion, confidence, symbols)
        patterns            = self.detect_recurring_patterns(dream_text)

        return {
            "emotion":             emotion,
            "confidence":          round(confidence, 4),
            "mood":                emotion,          # alias for frontend
            "emotion_score":       round(confidence, 4),
            "summary":             summary,
            "interpretation":      interpretation,
            "symbols":             [s["symbol"] for s in symbols],
            "symbol_details":      symbols,
            "dream_score":         round(dream_score, 2),
            "recurring_patterns":  patterns,
        }

    def analyze_emotion(self, dream_text: str) -> tuple[str, float]:
        """
        Score each emotion category against the dream text.
        Returns (dominant_emotion, confidence ∈ [0, 1]).
        """
        tokens = self._tokenize(dream_text)
        scores: dict[str, int] = Counter()

        for emotion, keywords in EMOTION_LEXICON.items():
            for kw in keywords:
                if kw in tokens:
                    scores[emotion] += tokens[kw]

        if not any(scores.values()):
            return "Mystery", 0.5

        top_emotion = max(scores, key=lambda e: scores[e])
        total = sum(scores.values())
        confidence = scores[top_emotion] / total if total else 0.5
        # Apply sigmoid-style scaling to avoid extremes
        confidence = self._scale_confidence(confidence)
        return top_emotion, confidence

    def extract_symbols(self, dream_text: str) -> list[dict[str, str]]:
        """
        Identify symbolic elements and attach their meanings.
        """
        text_lower = dream_text.lower()
        found: list[dict[str, str]] = []

        for symbol, meaning in SYMBOL_MEANINGS.items():
            # Match whole words / common inflections
            pattern = rf"\b{re.escape(symbol)}s?\b"
            if re.search(pattern, text_lower):
                found.append({"symbol": symbol, "meaning": meaning})

        # Cap at 8 most relevant symbols
        return found[:8]

    def generate_summary(self, dream_text: str, emotion: str) -> str:
        """
        Create a concise 2-3 sentence summary of the dream.
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", dream_text) if len(s.strip()) > 20]
        n = len(sentences)

        if n == 0:
            core = dream_text[:120]
        elif n == 1:
            core = sentences[0]
        else:
            # First sentence + (last sentence if text is long)
            core = sentences[0]
            if n >= 3:
                core += ". " + sentences[-1]

        return (
            f"A {emotion.lower()}-toned dream in which {core.lower().rstrip('.')}. "
            f"The narrative carries a strong {emotion.lower()} quality, reflecting "
            f"subconscious themes that your mind is actively processing."
        )

    def generate_interpretation(
        self,
        dream_text: str,
        emotion: str,
        symbols: list[dict[str, str]],
    ) -> str:
        """
        Produce a personalised Jungian-style interpretation.
        """
        import random

        templates = INTERPRETATION_TEMPLATES.get(emotion, INTERPRETATION_TEMPLATES["Mystery"])
        base = random.choice(templates)  # noqa: S311

        if symbols:
            top_syms = symbols[:3]
            sym_text = ", ".join(
                f"the symbol of {s['symbol']} (representing {s['meaning']})" for s in top_syms
            )
            base += f" Key symbols include {sym_text}."

        return base

    def detect_recurring_patterns(self, dream_text: str) -> list[str]:
        """
        Detect common archetypal dream patterns.
        """
        text_lower = dream_text.lower()
        patterns: list[str] = []

        pattern_map = {
            "Chase / pursuit":         r"\b(chase|chased|run|running|flee|fleeing|escape)\b",
            "Flying / levitation":     r"\b(fly|flying|float|floating|soar|soaring|levitate)\b",
            "Falling":                 r"\b(fall|falling|fell|drop|dropping|plunge)\b",
            "Teeth / body anxiety":    r"\b(teeth|tooth|hair|falling out|lost|crumbling)\b",
            "Being late / unprepared": r"\b(late|exam|test|unprepared|forgot|missing)\b",
            "Lost / searching":        r"\b(lost|search|find|look|wander|maze|labyrinth)\b",
            "Water immersion":         r"\b(swim|swimming|drown|ocean|sea|flood|wave)\b",
            "Meeting the deceased":    r"\b(dead|deceased|died|ghost|spirit|ancestor)\b",
        }

        for label, regex in pattern_map.items():
            if re.search(regex, text_lower):
                patterns.append(label)

        return patterns

    def calculate_dream_score(
        self,
        dream_text: str,
        emotion: str,
        confidence: float,
        symbols: list[dict[str, str]],
    ) -> float:
        """
        Return a dream score between 0 and 100 based on multiple factors.
        """
        # Length richness (10–500 words → 0–30 pts)
        word_count = len(dream_text.split())
        length_score = min(30.0, (word_count / 500) * 30)

        # Emotional intensity (confidence → 0–25 pts)
        emotion_score = confidence * 25

        # Symbolic density (symbols → 0–25 pts)
        symbol_score = min(25.0, len(symbols) * 3.1)

        # Vocabulary diversity (0–20 pts)
        words = re.findall(r"\b[a-z]+\b", dream_text.lower())
        diversity = len(set(words)) / max(len(words), 1)
        diversity_score = diversity * 20

        total = length_score + emotion_score + symbol_score + diversity_score
        return round(min(100.0, max(0.0, total)), 2)

    # ── Internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> Counter:
        """Lower-case word frequency counter."""
        words = re.findall(r"\b[a-z]+\b", text.lower())
        return Counter(words)

    @staticmethod
    def _scale_confidence(raw: float) -> float:
        """Map raw ratio to [0.30, 0.97] with soft clipping."""
        scaled = 0.30 + (raw * 0.67)
        return round(min(0.97, max(0.30, scaled)), 4)
