# Presentation outline — personalize after live validation

## Customer walkthrough (at most 5 minutes)
- State the problem: reproduce the wind forecast available when purchasing for the following day.
- Explain scenario cutoff and demonstrate a live-validated January day.
- Interpret the comparison chart, MAE/bias, and matched coverage without hiding missing data.
- Switch to January summary if validated; inspect one decision day.
- Open an interval audit trail; show publication <= cutoff.
- Export data; explain limitations. Do not invent findings.

## Technical walkthrough (at most 5 minutes)
- React -> job API -> Elexon -> UTC normalization -> latest-eligible selection -> exact/honest alignment -> metrics.
- Show cutoff equality test, conflict exclusion and incomplete actuals handling.
- Explain month aggregation, failed-day denominator and asynchronous job flow.
- Show real local test/build/live-check results, not merely the generated validation record.
- Explain single-worker job limitation, bounded lookback and actual revision policy.
- Disclose AI assistance and demonstrate that you understand and reviewed the code.

Linked video instructions and form are not reviewed yet. Follow them before recording/submitting.
