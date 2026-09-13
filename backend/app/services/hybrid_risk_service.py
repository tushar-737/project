from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HybridRiskResult:
    score: float
    level: str
    ml_score: float
    satellite_score: float
    ml_weight: float
    satellite_weight: float
    satellite_used: bool
    explanation: str

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level,
            "ml_score": self.ml_score,
            "satellite_score": self.satellite_score,
            "ml_weight": self.ml_weight,
            "satellite_weight": self.satellite_weight,
            "satellite_used": self.satellite_used,
            "explanation": self.explanation,
        }


def get_risk_level(score: float) -> str:
    if score < 25:
        return "LOW"
    elif score < 50:
        return "MODERATE"
    elif score < 75:
        return "HIGH"

    return "CRITICAL"


def calculate_hybrid_risk(
    ml_score: float,
    satellite_score: float | None,
    satellite_data_mode: str | None = None,
    freshness_status: str | None = None,
) -> HybridRiskResult:

    ml_score = max(
        0.0,
        min(
            100.0,
            float(ml_score),
        ),
    )

    if satellite_score is None:
        return HybridRiskResult(
            score=round(ml_score, 2),
            level=get_risk_level(ml_score),
            ml_score=round(ml_score, 2),
            satellite_score=0.0,
            ml_weight=1.0,
            satellite_weight=0.0,
            satellite_used=False,
            explanation=(
                "Final risk is based on the existing AI/ML model "
                "because satellite data was unavailable."
            ),
        )

    satellite_score = max(
        0.0,
        min(
            100.0,
            float(satellite_score),
        ),
    )

    ml_weight = 0.85
    satellite_weight = 0.15

    if satellite_data_mode == "REAL_SATELLITE":
        satellite_weight = 0.15

    elif satellite_data_mode == "ENVIRONMENTAL_FALLBACK":
        satellite_weight = 0.05

    else:
        satellite_weight = 0.05

    if freshness_status == "FRESH":
        pass

    elif freshness_status == "RECENT":
        satellite_weight *= 0.80

    elif freshness_status == "STALE":
        satellite_weight *= 0.50

    elif freshness_status == "OLD":
        satellite_weight *= 0.20

    elif freshness_status in (
        "UNKNOWN",
        "NO_REAL_OBSERVATION",
    ):
        satellite_weight *= 0.30

    ml_weight = 1.0 - satellite_weight

    hybrid_score = (
        ml_score * ml_weight
        +
        satellite_score * satellite_weight
    )

    hybrid_score = max(
        0.0,
        min(
            100.0,
            hybrid_score,
        ),
    )

    hybrid_level = get_risk_level(
        hybrid_score
    )

    explanation = (
        f"Hybrid risk combines the existing AI/ML model "
        f"({round(ml_weight * 100)}%) with satellite intelligence "
        f"({round(satellite_weight * 100)}%)."
    )

    return HybridRiskResult(
        score=round(
            hybrid_score,
            2,
        ),
        level=hybrid_level,
        ml_score=round(
            ml_score,
            2,
        ),
        satellite_score=round(
            satellite_score,
            2,
        ),
        ml_weight=round(
            ml_weight,
            3,
        ),
        satellite_weight=round(
            satellite_weight,
            3,
        ),
        satellite_used=(
            satellite_weight > 0
        ),
        explanation=explanation,
    )