"""
Dream Visualizer AI - Image Generation Engine
Converts dream text into richly-detailed cinematic prompts.
Compatible with Stable Diffusion, DALL·E, Midjourney, etc.
"""

import hashlib
import logging
import re
import urllib.parse

logger = logging.getLogger("dream_visualizer.image_generator")

# ── Style modifier libraries ──────────────────────────────────────────────────

STYLE_MODIFIERS: dict[str, dict] = {
    "fantasy": {
        "prefix":  "Epic fantasy artwork,",
        "suffix":  "magical particles, ethereal glow, concept art by Greg Rutkowski, artstation, 8K resolution",
        "palette": "rich jewel tones, mystical purples, golden light",
        "mood":    "magical, wondrous, otherworldly",
    },
    "sci-fi": {
        "prefix":  "Cinematic science-fiction scene,",
        "suffix":  "neon lights, holographic interfaces, volumetric fog, blade runner aesthetic, CG render, ultra-detailed",
        "palette": "cyan, electric blue, neon orange, deep black",
        "mood":    "futuristic, technological, vast",
    },
    "nightmare": {
        "prefix":  "Dark surrealist nightmare painting,",
        "suffix":  "twisted shadows, unsettling atmosphere, by Zdzisław Beksiński, horror art, intricate detail, deep contrast",
        "palette": "desaturated greys, blood red, sickly yellows",
        "mood":    "ominous, oppressive, surreal dread",
    },
    "adventure": {
        "prefix":  "Epic adventure cinematic scene,",
        "suffix":  "dramatic lighting, heroic composition, golden hour, by concept artist Craig Mullins, masterpiece",
        "palette": "warm amber, lush greens, sky blue",
        "mood":    "courageous, expansive, dynamic",
    },
    "romance": {
        "prefix":  "Soft romantic impressionist scene,",
        "suffix":  "bokeh, warm golden glow, dreamy soft-focus, painterly brushwork, tender mood",
        "palette": "rose pinks, warm creams, soft lavenders",
        "mood":    "tender, intimate, luminous",
    },
    "mystery": {
        "prefix":  "Atmospheric mystery illustration,",
        "suffix":  "chiaroscuro lighting, moonlight, fog, detailed environment, by Ruan Jia, enigmatic mood",
        "palette": "midnight blues, silver mist, deep indigos",
        "mood":    "enigmatic, hushed, suspenseful",
    },
    # Fallback – maps any unrecognised mood
    "default": {
        "prefix":  "Dreamlike surrealist artwork,",
        "suffix":  "painterly atmosphere, masterpiece quality, highly detailed, award-winning digital art",
        "palette": "rich and evocative tones",
        "mood":    "dreamlike, immersive",
    },
}

# Emotion → style mapping (from DreamAnalyzer output)
EMOTION_TO_STYLE: dict[str, str] = {
    "Happy":     "fantasy",
    "Fear":      "nightmare",
    "Adventure": "adventure",
    "Mystery":   "mystery",
    "Love":      "romance",
    "Anxiety":   "nightmare",
    "Excitement":"adventure",
    "Sadness":   "romance",
}

# Cinematic quality boosters appended to every prompt
UNIVERSAL_QUALITY_TAGS = (
    "cinematic composition, ultra-detailed, masterpiece, "
    "stunning visual fidelity, hyperrealistic textures, depth of field"
)


# ── Key-scene extractor ───────────────────────────────────────────────────────

def _extract_key_scenes(dream_text: str, max_elements: int = 5) -> list[str]:
    """
    Extract the most visually evocative phrases from the dream text.
    Returns up to `max_elements` noun/verb phrases.
    """
    # Simple heuristic: grab noun phrases preceded by 'I was', 'there was', etc.
    patterns = [
        r"i (?:was |saw |found |felt )([a-z\s]+)",
        r"there (?:was |were )(?:a |an )?([a-z\s]+)",
        r"a ([a-z\s]+ (?:appeared|flew|stood|rose|emerged|glowed|shimmered))",
        r"(?:the |a |an )([a-z\s]{5,40})(?:,|\.|!|\?|$)",
    ]
    scenes: list[str] = []
    text_lower = dream_text.lower()

    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            m = m.strip()
            if 3 < len(m) < 60:
                scenes.append(m)
        if len(scenes) >= max_elements:
            break

    # Fallback: use first two sentences if nothing matched
    if not scenes:
        sents = re.split(r"[.!?]", dream_text)
        scenes = [s.strip()[:80] for s in sents if len(s.strip()) > 15][:2]

    return scenes[:max_elements]


# ── Main generator class ───────────────────────────────────────────────────────

class DreamImageGenerator:
    """
    Converts free-form dream text + mood into a detailed image generation prompt.
    """

    def generate_dream_prompt(self, dream_text: str, mood: str = "mystery") -> str:
        """
        Build a richly detailed, style-appropriate image prompt.

        Args:
            dream_text: Raw dream description.
            mood:       Either an emotion label (Happy / Fear / …)
                        or a direct style key (fantasy / sci-fi / …).

        Returns:
            A single string prompt ready for any diffusion model.
        """
        # Resolve style
        style_key = EMOTION_TO_STYLE.get(mood, mood.lower())
        style = STYLE_MODIFIERS.get(style_key, STYLE_MODIFIERS["default"])

        # Extract visual scenes
        scenes = _extract_key_scenes(dream_text)
        core_scene = ", ".join(scenes) if scenes else dream_text[:120]

        # Compose prompt
        prompt_parts = [
            style["prefix"],
            core_scene,
            f"palette: {style['palette']}",
            f"mood: {style['mood']}",
            style["suffix"],
            UNIVERSAL_QUALITY_TAGS,
        ]
        prompt = " ".join(p.strip(", ") for p in prompt_parts if p)

        # Clean up double spaces / punctuation
        prompt = re.sub(r"\s{2,}", " ", prompt).strip()
        logger.info("Generated prompt (%d chars) for mood=%s", len(prompt), mood)
        return prompt

    # ── Placeholder image URL ──────────────────────────────────────────────

    def get_placeholder_url(self, prompt: str) -> str:
        """
        Return a deterministic placeholder image URL for the given prompt.
        In production, replace this method body with a real API call
        (Replicate, OpenAI Images, Stability AI, etc.).

        Uses Picsum with a hash-derived seed for stable per-prompt images.
        """
        seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16) % 1000  # noqa: S324
        return f"https://picsum.photos/seed/{seed}/800/600"

    # ── Convenience: build prompt from full analysis dict ─────────────────

    def prompt_from_analysis(self, analysis: dict) -> str:
        """
        Build a prompt directly from the dict returned by DreamAnalyzer.
        """
        return self.generate_dream_prompt(
            dream_text=analysis.get("dream_text", ""),
            mood=analysis.get("emotion", "mystery"),
        )
