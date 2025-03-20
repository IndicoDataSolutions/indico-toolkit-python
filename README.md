# Indico Toolkit

**This repository contains software that is not officially supported by Indico. It may
  be outdated or contain bugs. The operations it performs are potentially destructive.
  Use at your own risk.**

Classes, functions, and abstractions for building workflows using the Indico IPA
(Intelligent Process Automation) platform.

- [Polling Classes](https://github.com/IndicoDataSolutions/indico-toolkit-python/tree/main/indico_toolkit/polling/__init__.py)
  that implement best-practices polling behavior for Auto Review and Downstream
  processes. Easily plug in business logic without the boilerplate.
- [Result File](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/results/__init__.py)
  and [Etl Output](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/etloutput/__init__.py)
  Data Classes that parse standard IPA JSON output into idiomatic, type-safe Python dataclasses.
- [Metrics Classes](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/metrics/__init__.py)
  to compare model performance, evaluate ground truth, and plot statistics.
- [Snapshot Classes](https://github.com/IndicoDataSolutions/indico-toolkit-python/blob/main/indico_toolkit/snapshots/snapshot.py)
  to concatenate, merge, filter, and manipulate snapshot CSVs.

...and more in the [Examples](https://github.com/IndicoDataSolutions/indico-toolkit-python/tree/main/examples) folder.


## Installation

**Indico Toolkit does not use semantic versioning.**

Indico Toolkit versions match the minimum IPA version required to use its functionality.
E.g. `indico-toolkit==6.14.0` makes use of functionality introduced in IPA 6.14, and
some functionality requires IPA 6.14 or later to use.

```bash
pip install indico-toolkit
```

Some functionality requires optional dependencies that can be installed with extras.

```bash
pip install 'indico-toolkit[all]'
pip install 'indico-toolkit[downloads]'
pip install 'indico-toolkit[examples]'
pip install 'indico-toolkit[metrics]'
pip install 'indico-toolkit[predictions]'
pip install 'indico-toolkit[snapshots]'
```


## Contributing

Indico Toolkit uses Poetry 2.X for package and dependency management.


### Setup

Clone the source repository with Git.

```bash
git clone git@github.com:IndicoDataSolutions/indico-toolkit-python.git
```

Install dependencies with Poetry.

```bash
poetry install
```

Formatting, linting, type checking, and tests are defined as
[Poe](https://poethepoet.natn.io/) tasks in `pyproject.toml`.

```bash
poetry poe {format,check,test,all}
```

Code changes or additions should pass `poetry poe all` before opening a PR.


### Tests

Indico Toolkit has three test suites: required unit tests, extra unit tests, and
integration tests.

By default, only required unit tests are executed. Extra unit tests and integration
tests are skipped.

```bash
poetry poe {test,all}
```

Extra unit tests are skipped when their dependencies are not installed. To execute extra
unit tests, install one or more extras and run the tests.

```bash
poetry install --all-extras
poetry poe {test,all}
```

Integration tests make API calls to an IPA environment and require a host and API token
to execute. These tests create datasets, setup workflows, and train models. **Expect
them to take tens of minutes to run.**

```bash
poetry poe test-integration \
    --host try.indico.io \
    --token indico_api_token.txt
```

Make liberal use of pytest's `--last-failed` and `--failed-first`
[flags](https://docs.pytest.org/en/stable/how-to/cache.html) to speed up integration
test execution when writing code.
