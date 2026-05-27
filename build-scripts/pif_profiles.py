#!/usr/bin/env python3
"""
Profile definitions for Planetary Infrastructure Framework tooling.

A profile describes an object family, not a single transformation script.  The
same command-line tools can analyze, split, generate and validate different
object families by loading one of these profiles.  Updating a future Stellaris
version should primarily mean updating these profiles and the small
profile-specific backend callbacks, not cloning every pipeline script.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pif_stellaris import (
    CANONICAL_REAL_CATEGORIES,
    CANONICAL_ZONE_CATEGORIES,
    CANONICAL_ZONE_SLOT_CATEGORIES,
    DISTRICT_CATEGORY_DISPLAY,
    ZONE_CATEGORY_DISPLAY,
    ZONE_SLOT_CATEGORY_DISPLAY,
    category_for_param,
    normalize_planet_modifier,
    normalize_zone_modifier,
    normalize_zone_slot_stmt,
    zone_category_for_param,
    zone_slot_category_for_param,
)
from pif_backends.buildings_common import (
    BUILDING_CATEGORY_DISPLAY,
    CANONICAL_BUILDING_CATEGORIES,
    building_category_for_param,
    normalize_building_stmt,
)
from pif_backends.jobs_common import (
    CANONICAL_JOB_CATEGORIES,
    JOB_CATEGORY_DISPLAY,
    job_category_for_param,
    normalize_job_stmt,
)


@dataclass(frozen=True)
class PifProfile:
    """Static configuration for one PIF object family."""

    name: str
    display_name: str
    object_label: str
    source_folder: str
    output_folder: str
    object_prefix: Optional[str]
    source_docs: List[str]
    canonical_categories: List[str]
    category_display: Dict[str, str]
    category_for_param: Callable[..., str]
    normalize_stmt: Callable
    generator_backend: str
    validator_backend: str
    default_output: str
    manifest_name: str
    validation_report_name: str
    supports_object_classes: bool = False
    object_file_prefix: str = "pif"
    variable_file_prefix: str = "pif"
    notes: List[str] = field(default_factory=list)


def _district_category(param: str, *, object_class: str = "real") -> str:
    """Adapter around the district category function."""
    return category_for_param(param, district_class=object_class)


def _zone_category(param: str, *, object_class: str = "zone") -> str:
    """Adapter around the zone category function."""
    return zone_category_for_param(param)


def _zone_slot_category(param: str, *, object_class: str = "zone_slot") -> str:
    """Adapter around the zone-slot category function."""
    return zone_slot_category_for_param(param)


def _building_category(param: str, *, object_class: str = "regular") -> str:
    """Adapter around the building category function."""
    return building_category_for_param(param)


def _job_category(param: str, *, object_class: str = "worker") -> str:
    """Adapter around the pop job category function."""
    return job_category_for_param(param)


PROFILES: Dict[str, PifProfile] = {
    "districts": PifProfile(
        name="districts",
        display_name="Districts",
        object_label="district",
        source_folder="districts",
        output_folder="districts",
        object_prefix="district_",
        source_docs=["districts/00_DOCUMENTATION.txt"],
        canonical_categories=CANONICAL_REAL_CATEGORIES,
        category_display=DISTRICT_CATEGORY_DISPLAY,
        category_for_param=_district_category,
        normalize_stmt=normalize_planet_modifier,
        generator_backend="pif_backends.districts_generate",
        validator_backend="pif_backends.districts_validate",
        default_output="/mnt/data/PIF_profiled_districts",
        manifest_name="pif_district_generation_manifest.json",
        validation_report_name="pif_district_validation_report.json",
        supports_object_classes=True,
        notes=[
            "Real districts use category inline scripts.",
            "District masks remain compact METADATA + MASK objects.",
            "planet_modifier is normalized into triggered_planet_modifier.",
        ],
    ),
    "zones": PifProfile(
        name="zones",
        display_name="Zones",
        object_label="zone",
        source_folder="zones",
        output_folder="zones",
        object_prefix=None,
        source_docs=["zones/99_HOW_TO_ZONE.txt"],
        canonical_categories=CANONICAL_ZONE_CATEGORIES,
        category_display=ZONE_CATEGORY_DISPLAY,
        category_for_param=_zone_category,
        normalize_stmt=normalize_zone_modifier,
        generator_backend="pif_backends.zones_generate",
        validator_backend="pif_backends.zones_validate",
        default_output="/mnt/data/PIF_profiled_zones",
        manifest_name="pif_zone_generation_manifest.json",
        validation_report_name="pif_zone_validation_report.json",
        notes=[
            "ZONE_CONFIG contains zone_sets and building compatibility lists.",
            "swap_type and swap_type_weight remain in METADATA.",
            "static zone modifiers are normalized into triggered equivalents.",
        ],
    ),
    "zone_slots": PifProfile(
        name="zone_slots",
        display_name="Zone Slots",
        object_label="zone_slot",
        source_folder="zone_slots",
        output_folder="zone_slots",
        object_prefix="slot_",
        source_docs=["zone_slots/99_HOW_TO_ZONE.txt"],
        canonical_categories=CANONICAL_ZONE_SLOT_CATEGORIES,
        category_display=ZONE_SLOT_CATEGORY_DISPLAY,
        category_for_param=_zone_slot_category,
        normalize_stmt=normalize_zone_slot_stmt,
        generator_backend="pif_backends.zone_slots_generate",
        validator_backend="pif_backends.zone_slots_validate",
        default_output="/mnt/data/PIF_profiled_zone_slots",
        manifest_name="pif_zone_slot_generation_manifest.json",
        validation_report_name="pif_zone_slot_validation_report.json",
        notes=[
            "Zone slots have no vanilla inline scripts and no scripted variables.",
            "start remains in METADATA; ZS_CONFIG and AVAILABILITY become category inline scripts.",
            "No statement-level normalizations are currently applied to zone slots.",
        ],
    ),
    "buildings": PifProfile(
        name="buildings",
        display_name="Buildings",
        object_label="building",
        source_folder="buildings",
        output_folder="buildings",
        object_prefix=None,
        source_docs=["buildings/00_example.txt"],
        canonical_categories=CANONICAL_BUILDING_CATEGORIES,
        category_display=BUILDING_CATEGORY_DISPLAY,
        category_for_param=_building_category,
        normalize_stmt=normalize_building_stmt,
        generator_backend="pif_backends.buildings_generate",
        validator_backend="pif_backends.buildings_validate",
        default_output="/mnt/data/PIF_profiled_buildings",
        manifest_name="pif_building_generation_manifest.json",
        validation_report_name="pif_building_validation_report.json",
        supports_object_classes=True,
        notes=[
            "Stage 4 loads all top-level common/buildings objects, not only building_* keys.",
            "Modifier carriers are classified by contents; mixed modifier blocks stay in TPM.",
            "Only meaningful numeric tuning values are moved to building variable files.",
        ],
    ),
    "jobs": PifProfile(
        name="jobs",
        display_name="Jobs",
        object_label="job",
        source_folder="pop_jobs",
        output_folder="pop_jobs",
        object_prefix=None,
        source_docs=["pop_jobs/000_pretriggers.txt"],
        canonical_categories=CANONICAL_JOB_CATEGORIES,
        category_display=JOB_CATEGORY_DISPLAY,
        category_for_param=_job_category,
        normalize_stmt=normalize_job_stmt,
        generator_backend="pif_backends.jobs_generate",
        validator_backend="pif_backends.jobs_validate",
        default_output="/mnt/data/PIF_profiled_jobs",
        manifest_name="pif_job_generation_manifest.json",
        validation_report_name="pif_job_validation_report.json",
        supports_object_classes=True,
        notes=[
            "Stage 5 loads all top-level common/pop_jobs objects, including jobs with no category field.",
            "Modifier carriers are classified by contents; mixed modifier blocks stay in TPM.",
            "Top-level job boolean flags are intentionally moved to job variable files.",
        ],
    ),
}


def get_profile(name: str) -> PifProfile:
    """Return a profile by name or raise a helpful error."""
    key = name.strip().lower()
    if key not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        raise SystemExit(f"Unknown PIF profile '{name}'. Valid profiles: {valid}")
    return PROFILES[key]


def list_profiles() -> List[str]:
    """Return all supported profile names."""
    return sorted(PROFILES)
