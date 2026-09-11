from dataclasses import dataclass


@dataclass
class EvidenceAnalysis:
    label: str
    confidence: float
    indicators: list[str]
    recommendation: str

    def as_dict(self):
        return {
            "label": self.label,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "recommendation": self.recommendation,
        }


def analyze_report(report_type: str, has_image: bool, has_video: bool):
    """
    Prototype evidence analysis.

    This provides an explainable evidence assessment based on
    the report type and available media.

    A real computer vision model can replace this later.
    """

    report_type = (report_type or "OTHER").upper()

    indicators = []

    if has_image:
        indicators.append("Photographic evidence provided")

    if has_video:
        indicators.append("Video evidence provided")

    if report_type == "LANDSLIDE":

        indicators.extend([
            "Reported landslide activity",
            "Potential soil displacement",
            "Possible debris movement",
        ])

        confidence = 0.82 if has_image else 0.65

        return EvidenceAnalysis(
            label="POSSIBLE_LANDSLIDE",
            confidence=confidence,
            indicators=indicators,
            recommendation=(
                "Send the report for field officer verification "
                "and inspect the affected area."
            ),
        )

    if report_type == "SLOPE_MOVEMENT":

        indicators.extend([
            "Reported slope movement",
            "Possible terrain instability",
        ])

        confidence = 0.78 if has_image else 0.60

        return EvidenceAnalysis(
            label="POSSIBLE_SLOPE_INSTABILITY",
            confidence=confidence,
            indicators=indicators,
            recommendation=(
                "Monitor the location and request field verification."
            ),
        )

    if report_type == "SLOPE_CRACK":

        indicators.extend([
            "Reported slope crack",
            "Potential ground instability",
        ])

        return EvidenceAnalysis(
            label="POSSIBLE_SLOPE_CRACK",
            confidence=0.75 if has_image else 0.58,
            indicators=indicators,
            recommendation=(
                "Inspect the slope for further crack development."
            ),
        )

    if report_type == "ROAD_BLOCKAGE":

        indicators.extend([
            "Reported road obstruction",
        ])

        return EvidenceAnalysis(
            label="ROAD_BLOCKAGE_REPORTED",
            confidence=0.85 if has_image else 0.65,
            indicators=indicators,
            recommendation=(
                "Verify the road condition and notify emergency services if required."
            ),
        )

    return EvidenceAnalysis(
        label="REQUIRES_VERIFICATION",
        confidence=0.50,
        indicators=indicators or ["Limited evidence available"],
        recommendation=(
            "Send this report for manual field officer verification."
        ),
    )