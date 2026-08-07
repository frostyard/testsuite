# Behave suite changes

When changing a suite, run the affected features against a live snosi machine:

```bash
PYTHONPATH=. python3 -m behave tests/<suite>/features/ --no-capture --tags ~@wip
```

Keep probes local to the image under test. Do not install packages other than
`python3-behave` to make a scenario pass.
