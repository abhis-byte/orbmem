# models/safety.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Callable, Optional, Dict


# ============================================================
# SAFETY EVENT DATA MODEL
# ============================================================

@dataclass
class SafetyEvent:
    text: str
    tag: str
    severity: float
    correction: Optional[str]
    details: Dict
    timestamp: str = datetime.utcnow().isoformat()


# ============================================================
# SAFETY RULE BASE CLASS
# ============================================================

class SafetyRule:
    """
    Base class for all safety rules.
    Each rule returns a list of SafetyEvent objects.
    """

    tag: str = "generic"
    severity: float = 0.0

    def check(self, text: str) -> List[SafetyEvent]:
        raise NotImplementedError("SafetyRule subclasses must implement check().")


# ============================================================
# EXAMPLE RULES FOR ORBMEM v1
# ============================================================

class ProfanityRule(SafetyRule):
    tag = "profanity"
    severity = 0.2

    BAD_WORDS = ["fuck", "shit", "bitch"]

    def check(self, text: str) -> List[SafetyEvent]:
        events = []
        lower = text.lower()
        for word in self.BAD_WORDS:
            if word in lower:
                events.append(
                    SafetyEvent(
                        text=text,
                        tag=self.tag,
                        severity=self.severity,
                        correction="Avoid using offensive language.",
                        details={"word": word},
                    )
                )
        return events


class ViolenceRule(SafetyRule):
    tag = "violence"
    severity = 0.6

    VIOLENT_PATTERNS = ["kill", "murder", "hurt badly"]

    def check(self, text: str) -> List[SafetyEvent]:
        events = []
        lower = text.lower()
        for pattern in self.VIOLENT_PATTERNS:
            if pattern in lower:
                events.append(
                    SafetyEvent(
                        text=text,
                        tag=self.tag,
                        severity=self.severity,
                        correction="Avoid harmful or violent expressions.",
                        details={"pattern": pattern},
                    )
                )
        return events


class SexualContentRule(SafetyRule):
    tag = "sexual_content"
    severity = 0.7

    PATTERNS = ["sex", "porn", "nude"]

    def check(self, text: str) -> List[SafetyEvent]:
        events = []
        lower = text.lower()
        for p in self.PATTERNS:
            if p in lower:
                events.append(
                    SafetyEvent(
                        text=text,
                        tag=self.tag,
                        severity=self.severity,
                        correction="Avoid inappropriate sexual content.",
                        details={"pattern": p},
                    )
                )
        return events


# ============================================================
# SAFETY RULE ENGINE (MASTER)
# ============================================================

class SafetyRuleEngine:
    """
    Applies multiple safety rules to text.
    """

    def __init__(self):
        self.rules: List[SafetyRule] = [
            ProfanityRule(),
            ViolenceRule(),
            SexualContentRule(),
        ]

    def apply(self, text: str) -> List[SafetyEvent]:
        results = []
        for rule in self.rules:
            results.extend(rule.check(text))
        return results
