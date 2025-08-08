"""
Centralized configuration for per-game constants.

Best practice: keep gameplay constants in one place and import where needed.
"""

from typing import Dict


GAME_CONSTANTS: Dict[str, Dict[str, int]] = {
    "chess": {"k_factor": 40},
    "pingpong": {"k_factor": 40},
    "backgammon": {"k_factor": 10},  # Requested: default 10
}


def get_k_factor(game: str) -> int:
    """Return the K-factor for the given game, defaulting to 40 if unknown."""
    game_key = (game or "").lower()
    return GAME_CONSTANTS.get(game_key, {}).get("k_factor", 40)

