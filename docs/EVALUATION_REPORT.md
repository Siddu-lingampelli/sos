# SilentSOS Level 10.2 Evaluation Report Template

## Overview

This document provides the evaluation framework and methodology for measuring SilentSOS system performance per Level 10.2 requirements from SOS_PLAN.md.

## Evaluation Metrics

### Vision Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Precision | TP / (TP + FP) | > 0.85 |
| Recall | TP / (TP + FN) | > 0.85 |
| F1-Score | 2 * (Precision * Recall) / (Precision + Recall) | > 0.85 |
| Fall Detection Accuracy | Correct fall detections / total fall events | > 0.90 |
| Detection Latency | Time from fall to alert (ms) | < 2000 ms |

### System Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| False Alarm Rate | FP / (FP + TN) | < 0.10 |
| Missed Event Rate | FN / (TP + FN) | < 0.10 |
| Detection Rate | TP / (TP + FN) | > 0.90 |
| End-to-End Latency | Time from event to dashboard notification | < 3000 ms |

## Test Scenarios

### Scenario A: Normal Walking
- **Expected**: NO ALERT
- **Ground Truth**: Person walking normally
- **Pass Criteria**: No alert generated

### Scenario B: Sitting
- **Expected**: NO ALERT
- **Ground Truth**: Person sitting down
- **Pass Criteria**: No alert generated

### Scenario C: Intentional Lying
- **Expected**: NO ALERT
- **Ground Truth**: Person lying down intentionally
- **Pass Criteria**: No emergency alert (monitoring allowed)

### Scenario D: Fall + Recovery
- **Expected**: NO ALERT (recovery clears)
- **Ground Truth**: Person falls then gets up quickly
- **Pass Criteria**: Alert may trigger but is cleared

### Scenario E: Fall + Inactivity
- **Expected**: ALERT
- **Ground Truth**: Person falls and remains motionless
- **Pass Criteria**: Alert generated with confidence > 70%

### Scenario F: Distress Keyword (Deferred)
- **Expected**: ALERT
- **Status**: Audio evaluation deferred per user request

### Scenario G: Fall + Distress (Deferred)
- **Expected**: ALERT
- **Status**: Audio evaluation deferred per user request

## Evaluation Methodology

### 1. Test Execution

Tests are run using simulated scenarios with known ground truth. Each scenario feeds controlled data to:
- FallDetector
- InactivityMonitor
- EmergencyEngine

The system output is compared against expected outcomes.

### 2. Metrics Calculation

```python
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

Where:
- TP = True Positive (expected alert, got alert)
- FP = False Positive (expected no alert, got alert)
- TN = True Negative (expected no alert, got no alert)
- FN = False Negative (expected alert, got no alert)

### 3. Threshold Sensitivity Analysis

Thresholds are swept to find optimal operating points:

**Fall Detection Thresholds:**
- FALL_ANGLE_THRESHOLD: 45° to 65° (step 5°)
- FALL_VERTICAL_VELOCITY: 0.15 to 0.25 (step 0.02)
- CONFIRM_FRAMES: 2 to 5

**Emergency Engine Thresholds:**
- ALERT_THRESHOLD: 60 to 80 (step 5)
- MONITOR_THRESHOLD: 30 to 50 (step 5)

For each threshold combination, precision/recall are calculated to generate ROC curves.

### 4. Latency Measurement

Latency is measured from:
- **Detection Latency**: Fall onset → FALL_CONFIRMED state
- **Processing Latency**: FALL_CONFIRMED → EmergencyEngine decision
- **End-to-End Latency**: Event → WebSocket notification

## Running Evaluation

### Quick Evaluation

```bash
cd tests
python evaluate.py --run
```

### Single Scenario

```bash
python evaluate.py --scenario inactivity
python evaluate.py --scenario walking
```

### View Last Results

```bash
python evaluate.py --last
```

## Results Format

### Database Storage

Results are stored in SQLite database `tests/metrics.db` with tables:
- `test_runs`: Run metadata
- `scenario_results`: Per-scenario outcomes
- `metrics_summary`: Overall metrics
- `threshold_analysis`: Threshold sweep results
- `confidence_distribution`: Score distributions

### Report Output

Reports generated to `tests/results/`:
- `latest_report.md`: Human-readable Markdown report
- `latest_metrics.json`: Machine-readable metrics export
- `report_{run_id}.md`: Historical reports

## Threshold Tuning Guidelines

### Increasing Precision (reduce false alarms)
- Increase FALL_ANGLE_THRESHOLD (e.g., 55° → 60°)
- Increase FALL_VERTICAL_VELOCITY (e.g., 0.20 → 0.22)
- Increase ALERT_THRESHOLD (e.g., 70 → 75)
- Increase CONFIRM_FRAMES (e.g., 3 → 4)

**Trade-off**: May increase missed events (lower recall)

### Increasing Recall (catch more emergencies)
- Decrease FALL_ANGLE_THRESHOLD (e.g., 55° → 50°)
- Decrease FALL_VERTICAL_VELOCITY (e.g., 0.20 → 0.18)
- Decrease ALERT_THRESHOLD (e.g., 70 → 65)
- Decrease CONFIRM_FRAMES (e.g., 3 → 2)

**Trade-off**: May increase false alarms (lower precision)

### Optimal Balance

Target F1-score > 0.85 with:
- Precision > 0.85 (minimize false alarms)
- Recall > 0.85 (minimize missed events)
- Latency < 2000ms (rapid response)

## Interpretation

### Good Performance
- Precision ≥ 0.90: Few false alarms
- Recall ≥ 0.90: Few missed emergencies
- F1 ≥ 0.90: Balanced performance
- Latency < 1500ms: Fast response

### Concerning Performance
- Precision < 0.70: Too many false alarms
- Recall < 0.70: Missing too many emergencies
- Latency > 3000ms: Slow response

### Actions Based on Results

**If False Alarms High:**
- Increase thresholds (see above)
- Improve pose tracking stability
- Add more confirmation frames

**If Missed Events High:**
- Decrease thresholds (see above)
- Check velocity window size
- Verify keypoint confidence settings

**If Latency High:**
- Optimize DETECT_STRIDE (increase if possible)
- Reduce IMGSZ if on CPU
- Profile fall detection logic

## Continuous Evaluation

Evaluation should be run:
1. After any threshold changes
2. Weekly during active development
3. Before each release
4. After system changes (camera, model updates)

Historical results enable trend analysis and regression detection.

## References

- SOS_PLAN.md Level 10.2
- SOS_Documentation.md Section 34
- tests/metrics_collector.py
- tests/evaluation_runner.py
