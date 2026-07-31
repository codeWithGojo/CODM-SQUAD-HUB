"""
Fixed tag vocabulary shown in the app's quick-tap UI for match logging
and manager VOD reviews. Keeping this as a single source of truth means
the AI prompt, the mobile UI, and validation all read from the same list
instead of drifting out of sync.
"""

STRENGTH_TAGS = [
    "strong_aim",
    "good_game_sense",
    "clutch_factor",
    "excellent_rotations",
    "strong_teamplay_comms",
    "high_impact_entries",
    "smart_utility_usage",
]

WEAKNESS_TAGS_MP = [
    "poor_aim_tracking",
    "weak_close_range",
    "weak_long_range",
    "bad_positioning",
    "slow_reactions",
    "over_peeking",
    "poor_utility_usage",
    "tunnel_vision",
    "bad_push_timing",
    "low_mid_round_impact",
]

WEAKNESS_TAGS_BR = [
    "poor_landing_early_deaths",
    "weak_mid_game_rotations",
    "bad_final_circle_decisions",
    "poor_endgame_positioning",
    "low_damage_output",
    "avoids_fights_too_much",
    "over_aggressive",
    "poor_third_partying",
    "weak_rotation_awareness",
    "bad_loadout_decisions",
]

PRIORITY_FOCUS_OPTIONS = [
    "aim_gun_skill",
    "positioning_movement",
    "decision_making_game_sense",
    "teamplay_communication",
    "utility_ability_usage",
    "mental_consistency",
]


def weakness_tags_for_mode(mode: str) -> list[str]:
    """Return the mode-appropriate weakness tag list (MP or BR)."""
    return WEAKNESS_TAGS_MP if mode == "MP" else WEAKNESS_TAGS_BR
