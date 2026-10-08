"""Metrics collector for evaluation runs."""
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Outcome(Enum):
    ALERT = "ALERT"
    NO_ALERT = "NO_ALERT"


@dataclass
class ScenarioResult:
    name: str
    expected: Outcome
    actual: Optional[Outcome] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    details: Dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.actual == self.expected

    @property
    def is_alert_scenario(self) -> bool:
        return self.expected == Outcome.ALERT


class MetricsCollector:
    """Collects metrics from evaluation runs."""

    def __init__(self):
        self.scenarios: List[ScenarioResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start_run(self):
        """Mark start of evaluation run."""
        self.start_time = time.time()
        self.scenarios = []

    def end_run(self):
        """Mark end of evaluation run."""
        self.end_time = time.time()

    def add_scenario(self, name: str, expected: Outcome, actual: Outcome,
                    confidence: Optional[float] = None, latency_ms: Optional[float] = None,
                    details: Optional[Dict] = None) -> ScenarioResult:
        """Add scenario result."""
        result = ScenarioResult(
            name=name,
            expected=expected,
            actual=actual,
            confidence=confidence,
            latency_ms=latency_ms,
            details=details or {}
        )

        # Calculate TP/FP/FN/TN
        if expected == Outcome.ALERT and actual == Outcome.ALERT:
            result.tp = 1
        elif expected == Outcome.NO_ALERT and actual == Outcome.ALERT:
            result.fp = 1
        elif expected == Outcome.ALERT and actual == Outcome.NO_ALERT:
            result.fn = 1
        elif expected == Outcome.NO_ALERT and actual == Outcome.NO_ALERT:
            result.tn = 1

        self.scenarios.append(result)
        return result

    def calculate_overall_metrics(self) -> Dict[str, float]:
        """Calculate overall precision, recall, F1, accuracy."""
        tp = sum(s.tp for s in self.scenarios)
        fp = sum(s.fp for s in self.scenarios)
        fn = sum(s.fn for s in self.scenarios)
        tn = sum(s.tn for s in self.scenarios)

        total = tp + fp + fn + tn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 0.0

        false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        missed_event_rate = fn / (tp + fn) if (tp + fn) > 0 else 0.0
        detection_rate = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # Latency stats
        latencies = [s.latency_ms for s in self.scenarios if s.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        return {
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'tn': tn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'accuracy': accuracy,
            'false_alarm_rate': false_alarm_rate,
            'missed_event_rate': missed_event_rate,
            'detection_rate': detection_rate,
            'avg_latency_ms': avg_latency,
            'total_scenarios': len(self.scenarios),
            'passed_scenarios': sum(1 for s in self.scenarios if s.passed),
            'failed_scenarios': sum(1 for s in self.scenarios if not s.passed)
        }

    def get_confidence_distribution(self) -> Dict[str, List[float]]:
        """Get confidence scores by outcome."""
        distribution = {
            Outcome.ALERT.value: [],
            Outcome.NO_ALERT.value: []
        }

        for scenario in self.scenarios:
            if scenario.confidence is not None and scenario.actual:
                distribution[scenario.actual.value].append(scenario.confidence)

        return distribution

    def get_scenario_report(self) -> str:
        """Generate detailed scenario report."""
        lines = []
        lines.append("# Scenario Results")
        lines.append("")

        for scenario in self.scenarios:
            status = "PASS" if scenario.passed else "FAIL"
            lines.append(f"## {scenario.name}")
            lines.append(f"**Status:** {status}")
            lines.append(f"**Expected:** {scenario.expected.value}")
            lines.append(f"**Actual:** {scenario.actual.value if scenario.actual else 'N/A'}")
            if scenario.confidence is not None:
                lines.append(f"**Confidence:** {scenario.confidence:.1%}")
            if scenario.latency_ms is not None:
                lines.append(f"**Latency:** {scenario.latency_ms:.1f} ms")
            lines.append(f"**TP/FP/FN/TN:** {scenario.tp}/{scenario.fp}/{scenario.fn}/{scenario.tn}")
            lines.append("")

        return "\n".join(lines)

    def get_summary_report(self) -> str:
        """Generate summary metrics report."""
        metrics = self.calculate_overall_metrics()

        lines = []
        lines.append("# Evaluation Summary")
        lines.append("")
        lines.append(f"**Total Scenarios:** {metrics['total_scenarios']}")
        lines.append(f"**Passed:** {metrics['passed_scenarios']}")
        lines.append(f"**Failed:** {metrics['failed_scenarios']}")
        lines.append("")
        lines.append("## Key Metrics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Precision | {metrics['precision']:.3f} |")
        lines.append(f"| Recall | {metrics['recall']:.3f} |")
        lines.append(f"| F1 Score | {metrics['f1_score']:.3f} |")
        lines.append(f"| Accuracy | {metrics['accuracy']:.3f} |")
        lines.append(f"| False Alarm Rate | {metrics['false_alarm_rate']:.3f} |")
        lines.append(f"| Missed Event Rate | {metrics['missed_event_rate']:.3f} |")
        lines.append(f"| Detection Rate | {metrics['detection_rate']:.3f} |")
        if metrics['avg_latency_ms'] is not None:
            lines.append(f"| Avg Latency | {metrics['avg_latency_ms']:.1f} ms |")
        lines.append("")
        lines.append("## Confusion Matrix")
        lines.append("")
        lines.append(f"| | Predicted Alert | Predicted No Alert |")
        lines.append(f"|-----------|---------------|-------------------|")
        lines.append(f"| Actual Alert | {metrics['tp']} | {metrics['fn']} |")
        lines.append(f"| Actual No Alert | {metrics['fp']} | {metrics['tn']} |")
        lines.append("")

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            lines.append(f"**Evaluation Duration:** {duration:.2f} seconds")

        return "\n".join(lines)

    def export_results(self) -> Dict:
        """Export results as dictionary."""
        metrics = self.calculate_overall_metrics()

        return {
            'scenarios': [
                {
                    'name': s.name,
                    'expected': s.expected.value,
                    'actual': s.actual.value if s.actual else None,
                    'confidence': s.confidence,
                    'latency_ms': s.latency_ms,
                    'passed': s.passed,
                    'tp': s.tp,
                    'fp': s.fp,
                    'fn': s.fn,
                    'tn': s.tn
                }
                for s in self.scenarios
            ],
            'metrics': metrics,
            'confidence_distribution': self.get_confidence_distribution()
        }


def calculate_precision_recall_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Calculate precision, recall, F1 from counts."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1
