"""Snow-Town inter-layer contracts.

Defines the data contracts that flow between layers:
- OutcomeRecord: Metroplex -> Sky-Lynx
- ImprovementRecommendation: Sky-Lynx -> (consumers)
- ResearchSignal: Research Agents -> Sky-Lynx
"""

from .improvement_recommendation import (
    EvidenceBasis,
    ImprovementRecommendation,
    RecommendationType,
    TargetScope,
)
from .outcome_record import OutcomeRecord, PipelineTrace, TerminalOutcome
from .research_signal import ResearchSignal, SignalRelevance, SignalSource
from .store import ContractStore

__all__ = [
    "OutcomeRecord",
    "PipelineTrace",
    "TerminalOutcome",
    "ImprovementRecommendation",
    "RecommendationType",
    "TargetScope",
    "EvidenceBasis",
    "ResearchSignal",
    "SignalRelevance",
    "SignalSource",
    "ContractStore",
]
