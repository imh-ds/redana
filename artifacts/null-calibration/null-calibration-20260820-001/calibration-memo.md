# Null-calibration diagnostic memo

Diagnostic outcome: **CALIBRATION QUESTION**

This is calibration evidence, not a revised Gate 0 conclusion.
No threshold, estimator, or fixture has changed.

## Distribution summaries

Shares apply the unchanged Gate 0 ten-replication classification rule to complete sequential batches; incomplete batches are not classified.

| Arm | Fixture | Evaluation rows | Count | Median observed | Observed 5th/95th | P-value 5th/50th/95th | Null-like / non-null / ambiguous shares |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fitted | F1 | 250 | 30 | 0.1005 | 0.0788 / 0.1427 | 0.0750 / 0.5975 / 0.9682 | 0.00 / 0.00 / 1.00 |
| fitted | F1 | 500 | 30 | 0.0696 | 0.0570 / 0.0918 | 0.1745 / 0.6375 / 0.9587 | 0.00 / 0.00 / 1.00 |
| fitted | F1 | 1000 | 30 | 0.0537 | 0.0398 / 0.0761 | 0.0550 / 0.4725 / 0.9665 | 0.33 / 0.00 / 0.67 |
| fitted | F1 | 2000 | 30 | 0.0396 | 0.0296 / 0.0526 | 0.0685 / 0.3900 / 0.9357 | 1.00 / 0.00 / 0.00 |
| fitted | F4 | 250 | 30 | 0.1094 | 0.0836 / 0.1514 | 0.0673 / 0.4625 / 0.9387 | 0.00 / 0.00 / 1.00 |
| fitted | F4 | 500 | 30 | 0.0782 | 0.0632 / 0.1384 | 0.0100 / 0.3850 / 0.8327 | 0.00 / 0.00 / 1.00 |
| fitted | F4 | 1000 | 30 | 0.0569 | 0.0414 / 0.0793 | 0.0545 / 0.3075 / 0.9375 | 0.00 / 0.00 / 1.00 |
| fitted | F4 | 2000 | 30 | 0.0388 | 0.0295 / 0.0534 | 0.0772 / 0.4700 / 0.9427 | 1.00 / 0.00 / 0.00 |
| fitted | F5 | 250 | 30 | 0.1039 | 0.0842 / 0.1600 | 0.0458 / 0.5100 / 0.9377 | 0.00 / 0.00 / 1.00 |
| fitted | F5 | 500 | 30 | 0.0752 | 0.0634 / 0.1185 | 0.0240 / 0.4950 / 0.8055 | 0.00 / 0.00 / 1.00 |
| fitted | F5 | 1000 | 30 | 0.0513 | 0.0396 / 0.0836 | 0.0573 / 0.5875 / 0.9655 | 0.33 / 0.00 / 0.67 |
| fitted | F5 | 2000 | 30 | 0.0396 | 0.0325 / 0.0538 | 0.0425 / 0.4250 / 0.8230 | 1.00 / 0.00 / 0.00 |
| fitted | F6 | 250 | 30 | 0.1100 | 0.0821 / 0.1386 | 0.1145 / 0.4300 / 0.9355 | 0.00 / 0.00 / 1.00 |
| fitted | F6 | 500 | 30 | 0.0750 | 0.0585 / 0.0990 | 0.0935 / 0.4700 / 0.9278 | 0.00 / 0.00 / 1.00 |
| fitted | F6 | 1000 | 30 | 0.0545 | 0.0414 / 0.0769 | 0.0625 / 0.4175 / 0.9477 | 0.33 / 0.00 / 0.67 |
| fitted | F6 | 2000 | 30 | 0.0376 | 0.0289 / 0.0565 | 0.0368 / 0.4950 / 0.9455 | 1.00 / 0.00 / 0.00 |
| reference | reference | 250 | 30 | 0.1066 | 0.0816 / 0.1399 | 0.0995 / 0.4675 / 0.9360 | 0.00 / 0.00 / 1.00 |
| reference | reference | 500 | 30 | 0.0762 | 0.0586 / 0.1080 | 0.0700 / 0.4575 / 0.9350 | 0.00 / 0.00 / 1.00 |
| reference | reference | 1000 | 30 | 0.0535 | 0.0408 / 0.0708 | 0.0800 / 0.4475 / 0.9467 | 0.00 / 0.00 / 1.00 |
| reference | reference | 2000 | 30 | 0.0370 | 0.0287 / 0.0520 | 0.0758 / 0.5525 / 0.9677 | 1.00 / 0.00 / 0.00 |

## Paired reference-versus-fitted comparisons

Each plot compares the independent standard-normal reference arm with every fitted fixture at the same evaluation size. Retained paths in the input records remain the underlying permutation and residual-sample evidence.
- plots/evaluation-250-reference-vs-fitted.png
- plots/evaluation-500-reference-vs-fitted.png
- plots/evaluation-1000-reference-vs-fitted.png
- plots/evaluation-2000-reference-vs-fitted.png

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
