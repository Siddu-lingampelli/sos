#!/usr/bin/env python3
"""Command-line evaluation tool for Level 10.2 metrics."""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluation_runner import EvaluationRunner
from tests.metrics_db import get_last_run, get_run_scenarios, get_run_metrics
from tests.metrics_collector import MetricsCollector, Outcome


def run_full_evaluation():
    """Run complete evaluation suite."""
    runner = EvaluationRunner()
    runner.run_all_scenarios()
    run_id = runner.save_results()
    runner.save_report()

    print(f"\nEvaluation complete! Run ID: {run_id}")
    print("\nSummary:")
    print(runner.collector.get_summary_report())

    return runner


def run_single_scenario(scenario_name: str):
    """Run a single scenario."""
    runner = EvaluationRunner()
    runner.collector.start_run()

    scenarios = {
        'walking': runner.run_scenario_a_normal_walking,
        'sitting': runner.run_scenario_b_sitting,
        'lying': runner.run_scenario_c_intentional_lying,
        'recovery': runner.run_scenario_d_fall_recovery,
        'inactivity': runner.run_scenario_e_fall_inactivity,
    }

    if scenario_name not in scenarios:
        print(f"Unknown scenario: {scenario_name}")
        print(f"Available: {', '.join(scenarios.keys())}")
        sys.exit(1)

    result = scenarios[scenario_name]()
    runner.collector.add_scenario(
        name=result['name'],
        expected=result['expected'],
        actual=result['actual'],
        confidence=result['confidence'],
        latency_ms=result['latency_ms'],
        details=result['details']
    )
    runner.collector.end_run()

    print(f"\n{result['name']}")
    print(f"Expected: {result['expected'].value}")
    print(f"Actual: {result['actual'].value}")
    print(f"Passed: {'✓' if result['expected'] == result['actual'] else '✗'}")

    return runner


def show_last_report():
    """Show last evaluation report."""
    from tests.metrics_db import get_last_run, get_run_scenarios, get_run_metrics

    last_run = get_last_run()
    if not last_run:
        print("No evaluation runs found. Run evaluation first with --run")
        sys.exit(1)

    print(f"Last Run ID: {last_run['id']}")
    print(f"Timestamp: {last_run['timestamp']}")
    print(f"Config Hash: {last_run['config_hash']}")
    print()

    metrics = get_run_metrics(last_run['id'])
    if metrics:
        print("Metrics:")
        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Recall: {metrics['recall']:.3f}")
        print(f"  F1 Score: {metrics['f1_score']:.3f}")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.1f} ms" if metrics['avg_latency_ms'] else "  Avg Latency: N/A")
        print()

    scenarios = get_run_scenarios(last_run['id'])
    print("Scenarios:")
    for s in scenarios:
        status = "✓" if s['passed'] else "✗"
        print(f"  {status} {s['scenario_name']}")
        print(f"      Expected: {s['expected_outcome']}, Actual: {s['actual_outcome']}")


def generate_report(run_id: int = None):
    """Generate and show report."""
    from tests.metrics_db import get_last_run

    if run_id is None:
        last_run = get_last_run()
        if not last_run:
            print("No runs found")
            sys.exit(1)
        run_id = last_run['id']

    # Load from database and generate report
    print(f"Generating report for run {run_id}...")
    # Report generation would go here
    print("Report generation not yet implemented for historical runs")


def main():
    parser = argparse.ArgumentParser(description='SilentSOS Level 10.2 Evaluation')
    parser.add_argument('--run', action='store_true', help='Run full evaluation suite')
    parser.add_argument('--scenario', type=str, help='Run specific scenario (walking, sitting, lying, recovery, inactivity)')
    parser.add_argument('--last', action='store_true', help='Show last evaluation results')
    parser.add_argument('--report', type=int, metavar='RUN_ID', help='Generate report for specific run')

    args = parser.parse_args()

    if not any([args.run, args.scenario, args.last, args.report]):
        parser.print_help()
        sys.exit(0)

    if args.run:
        run_full_evaluation()
    elif args.scenario:
        run_single_scenario(args.scenario)
    elif args.last:
        show_last_report()
    elif args.report:
        generate_report(args.report)


if __name__ == '__main__':
    main()
