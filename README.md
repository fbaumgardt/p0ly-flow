# p0ly-flow

Snakemake orchestration pipeline for p0ly EEG analysis.

## Quick Start

```bash
# Install (including p0ly-utils from sibling directory)
uv add --path ../p0ly-eeg
uv sync

# Validate
snakemake -n
snakemake --lint
```

## See Also

- p0ly-eeg (core library)
- scrum/ (project management vault)
