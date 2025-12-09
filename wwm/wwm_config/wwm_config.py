from dataclasses import dataclass
import yaml
import logging


@dataclass
class MaterialFarmConfig:
    app_title: str

    material_match_threshold: float
    waypoint_match_threshold: float
    visited_match_threshold: float

    top_n_closest: int

    seconds_between_actions: int
    seconds_for_each_material: int
    seconds_till_revisit: int
    seconds_for_loading_screen: int

    key_stop_script: str
    key_escape: str
    key_wayfinder: str
    key_confirm: str
    key_map: str
    key_character_pickup: str
    key_spirited_courser_pickup: str


def load_config(path="config.yaml") -> MaterialFarmConfig:

    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    return MaterialFarmConfig(
        app_title=cfg.get("app_title", "Where Winds Meet"),
        material_match_threshold=cfg.get("material_match_threshold", 0.65),
        waypoint_match_threshold=cfg.get("waypoint_match_threshold", 0.6),
        visited_match_threshold=cfg.get("visited_match_threshold", 0.95),
        top_n_closest=cfg.get("top_n_closest", 3),
        seconds_between_actions=cfg.get("seconds_between_actions", 2),
        seconds_for_each_material=cfg.get("seconds_for_each_material", 60),
        seconds_till_revisit=cfg.get("seconds_till_revisit", 300),
        seconds_for_loading_screen=cfg.get("seconds_for_loading_screen", 10),
        key_stop_script=cfg.get("key_stop_script", "F3"),
        key_escape=cfg.get("key_escape", "{ESC}"),
        key_wayfinder=cfg.get("key_wayfinder", "v"),
        key_confirm=cfg.get("key_confirm", " "),
        key_map=cfg.get("key_map", "m"),
        key_character_pickup=cfg.get("key_character_pickup", "f"),
        key_spirited_courser_pickup=cfg.get(
            "key_spirited_courser_pickup", "z"),
    )
