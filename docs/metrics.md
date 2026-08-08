# Project metrics

## Pull request acceptance

The pull request acceptance rate measures how often resolved pull requests are
merged:

```text
accepted PRs / (accepted PRs + closed, unmerged PRs) x 100
```

An accepted PR is any pull request merged during the reporting period. A
rejected PR is a pull request closed without merging during that period. Open
pull requests are excluded.

Report the metric monthly using UTC calendar months and GitHub pull request
data. Assign each pull request to the month in which it was merged or closed,
and report the accepted and closed-unmerged counts with the percentage so
changes in review volume remain visible.
