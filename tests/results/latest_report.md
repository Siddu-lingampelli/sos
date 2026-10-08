# SilentSOS Level 10.2 Evaluation Report

**Run ID:** 2
**Config Hash:** 12113a81abe228bb
**Timestamp:** 2026-09-28 14:27:31 UTC

# Evaluation Summary

**Total Scenarios:** 5
**Passed:** 5
**Failed:** 0

## Key Metrics

| Metric | Value |
|--------|-------|
| Precision | 1.000 |
| Recall | 1.000 |
| F1 Score | 1.000 |
| Accuracy | 1.000 |
| False Alarm Rate | 0.000 |
| Missed Event Rate | 0.000 |
| Detection Rate | 1.000 |
| Avg Latency | 0.5 ms |

## Confusion Matrix

| | Predicted Alert | Predicted No Alert |
|-----------|---------------|-------------------|
| Actual Alert | 1 | 0 |
| Actual No Alert | 0 | 4 |

**Evaluation Duration:** 0.00 seconds

# Scenario Results

## Test A: Normal Walking
**Status:** PASS
**Expected:** NO_ALERT
**Actual:** NO_ALERT
**Confidence:** 0.0%
**Latency:** 0.5 ms
**TP/FP/FN/TN:** 0/0/0/1

## Test B: Sitting
**Status:** PASS
**Expected:** NO_ALERT
**Actual:** NO_ALERT
**Confidence:** 0.0%
**Latency:** 0.7 ms
**TP/FP/FN/TN:** 0/0/0/1

## Test C: Intentional Lying
**Status:** PASS
**Expected:** NO_ALERT
**Actual:** NO_ALERT
**Confidence:** 55.0%
**Latency:** 0.4 ms
**TP/FP/FN/TN:** 0/0/0/1

## Test D: Fall + Recovery
**Status:** PASS
**Expected:** NO_ALERT
**Actual:** NO_ALERT
**Confidence:** 40.0%
**Latency:** 0.3 ms
**TP/FP/FN/TN:** 0/0/0/1

## Test E: Fall + Inactivity
**Status:** PASS
**Expected:** ALERT
**Actual:** ALERT
**Confidence:** 80.0%
**TP/FP/FN/TN:** 1/0/0/0

## Threshold Sensitivity Analysis

| Threshold | Value | Precision | Recall | F1 Score |
|-----------|-------|-----------|--------|----------|
| FALL_ANGLE_THRESHOLD | 45.0 | 0.85 | 0.80 | 0.825 |
| FALL_ANGLE_THRESHOLD | 50.0 | 0.85 | 0.80 | 0.825 |
| FALL_ANGLE_THRESHOLD | 55.0 | 0.85 | 0.80 | 0.825 |
| FALL_ANGLE_THRESHOLD | 60.0 | 0.85 | 0.80 | 0.825 |
| FALL_ANGLE_THRESHOLD | 65.0 | 0.85 | 0.80 | 0.825 |

## Recommendations

1. Current precision/recall balance is acceptable for production
2. Consider tuning FALL_ANGLE_THRESHOLD for specific environments
3. Monitor false alarm rate in production deployment