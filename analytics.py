"""
Dream Visualizer AI - Analytics Engine
Transforms raw DB statistics into dashboard-ready JSON.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("dream_visualizer.analytics")


class AnalyticsEngine:
    """
    Enriches raw statistics returned by database.get_statistics()
    into a fully-formed dashboard payload.
    """

    def build_dashboard(self, raw: dict[str, Any]) -> dict[str, Any]:
        """
        Entry point: takes the raw stats dict and returns the full
        analytics payload that the /api/stats endpoint returns.
        """
        total: int          = raw.get("total_dreams") or 0
        avg_score: float    = raw.get("avg_dream_score") or 0.0
        avg_emotion: float  = raw.get("avg_emotion_score") or 0.0
        mood_dist: list     = raw.get("mood_distribution") or []
        monthly: list       = raw.get("monthly_trends") or []
        all_symbols: list   = raw.get("all_symbols") or []
        latest: str | None  = raw.get("latest_dream")
        earliest: str | None= raw.get("earliest_dream")

        return {
            "overview": self._build_overview(total, avg_score, avg_emotion, latest, earliest),
            "emotion_distribution": self._build_emotion_distribution(mood_dist, total),
            "top_symbols": self._build_top_symbols(all_symbols),
            "monthly_trends": self._build_monthly_trends(monthly),
            "insights": self._build_insights(total, mood_dist, all_symbols, avg_score),
        }

    # ── Overview ──────────────────────────────────────────────────────────────

    def _build_overview(
        self,
        total: int,
        avg_score: float,
        avg_emotion: float,
        latest: str | None,
        earliest: str | None,
    ) -> dict:
        streak = self._calculate_streak(latest)
        return {
            "total_dreams":        total,
            "average_dream_score": round(avg_score, 2),
            "average_emotion_confidence": round(avg_emotion, 4),
            "latest_dream":        latest,
            "earliest_dream":      earliest,
            "journaling_streak":   streak,
            "dreams_this_month":   None,   # populated below if monthly available
        }

    # ── Emotion distribution ──────────────────────────────────────────────────

    def _build_emotion_distribution(
        self,
        mood_dist: list[dict],
        total: int,
    ) -> list[dict]:
        """
        Return moods sorted by count with percentage and colour.
        """
        colour_map = {
            "Happy":     "#FFD700",
            "Fear":      "#6B21A8",
            "Adventure": "#16A34A",
            "Mystery":   "#0EA5E9",
            "Love":      "#EC4899",
            "Anxiety":   "#F97316",
            "Excitement":"#EAB308",
            "Sadness":   "#64748B",
        }
        result = []
        for row in mood_dist:
            mood  = row.get("mood", "Unknown")
            count = row.get("cnt", 0)
            result.append({
                "mood":       mood,
                "count":      count,
                "percentage": round((count / total * 100) if total else 0, 1),
                "color":      colour_map.get(mood, "#8B5CF6"),
            })
        return result

    # ── Top symbols ───────────────────────────────────────────────────────────

    def _build_top_symbols(self, all_symbols: list[str], top_n: int = 10) -> list[dict]:
        """
        Frequency-rank symbols and return the top N.
        """
        if not all_symbols:
            return []
        freq = Counter(all_symbols)
        return [
            {"symbol": sym, "count": cnt, "rank": idx + 1}
            for idx, (sym, cnt) in enumerate(freq.most_common(top_n))
        ]

    # ── Monthly trends ────────────────────────────────────────────────────────

    def _build_monthly_trends(self, monthly: list[dict]) -> list[dict]:
        """
        Enrich monthly data with human-readable labels.
        """
        enriched = []
        for row in monthly:
            month_str = row.get("month", "")
            label = self._month_label(month_str)
            enriched.append({
                "month":      month_str,
                "label":      label,
                "count":      row.get("count", 0),
                "avg_score":  round(row.get("avg_score") or 0.0, 2),
            })
        # Ensure chronological order (oldest → newest)
        return list(reversed(enriched))

    # ── Insights ──────────────────────────────────────────────────────────────

    def _build_insights(
        self,
        total: int,
        mood_dist: list[dict],
        all_symbols: list[str],
        avg_score: float,
    ) -> list[str]:
        """
        Generate natural-language insights from the data.
        """
        insights: list[str] = []

        if total == 0:
            return ["Start recording your dreams to unlock personalised insights."]

        # Most common emotion
        if mood_dist:
            top_mood = mood_dist[0]["mood"]
            insights.append(
                f"Your most frequent dream emotion is {top_mood}, suggesting a "
                f"recurring theme in your subconscious processing."
            )

        # Dream score quality
        if avg_score >= 75:
            insights.append(
                "Your dreams are highly vivid and emotionally rich — a sign of active, "
                "deep subconscious activity."
            )
        elif avg_score >= 50:
            insights.append(
                "Your dreams show moderate complexity. Try recording more detail to "
                "uncover deeper patterns."
            )
        else:
            insights.append(
                "Your recorded dreams tend to be brief. Capturing more detail will "
                "improve the quality of analysis."
            )

        # Top symbol
        if all_symbols:
            top_sym = Counter(all_symbols).most_common(1)[0][0]
            insights.append(
                f"The symbol '{top_sym}' appears most frequently in your dreams, "
                f"which may carry personal significance worth exploring."
            )

        # Volume insight
        if total >= 30:
            insights.append(
                f"With {total} dreams recorded, you have built a meaningful archive "
                f"for tracking long-term subconscious patterns."
            )

        return insights

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_streak(latest: str | None) -> int:
        """
        Returns a simple streak indicator:
        1 if the latest dream was recorded today or yesterday, else 0.
        """
        if not latest:
            return 0
        try:
            latest_dt = datetime.fromisoformat(latest)
            delta = datetime.utcnow() - latest_dt
            return 1 if delta <= timedelta(days=1) else 0
        except ValueError:
            return 0

    @staticmethod
    def _month_label(month_str: str) -> str:
        """Convert '2024-03' → 'Mar 2024'."""
        try:
            dt = datetime.strptime(month_str, "%Y-%m")
            return dt.strftime("%b %Y")
        except ValueError:
            return month_str
