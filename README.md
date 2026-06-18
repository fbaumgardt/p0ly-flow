# p0ly-flow

Snakemake orchestration pipeline for p0ly EEG analysis.

## Quick Start

```bash
# Install (resolves p0ly-utils from the sibling p0ly-eeg via path source)
uv sync

# Validate
uv run snakemake -n
uv run snakemake --lint
```

## See Also

- p0ly-eeg (core library)
- scrum/ (project management vault)
