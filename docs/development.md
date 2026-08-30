# Development

## Setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency management,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting,
[mypy](https://mypy-lang.org/) for type checking and
[pytest](https://docs.pytest.org/) for tests.

```shell
git clone https://github.com/ngine-io/chaotic
cd chaotic
make install
```

`make help` lists every available target. The most used ones:

| Target           | What it does                                        |
| ---------------- | --------------------------------------------------- |
| `make lint`      | Ruff lint plus a formatting check                   |
| `make format`    | Apply ruff autofixes and formatting                 |
| `make typecheck` | Run mypy in strict mode                             |
| `make test`      | Run the test suite                                  |
| `make coverage`  | Run the test suite with a coverage report           |
| `make check`     | Everything CI runs                                  |
| `make build`     | Build the sdist and the wheel into `dist/`          |
| `make docs`      | Build this documentation into `site/`               |

Running the CLI from a checkout:

```shell
uv run chaotic-ngine --config examples/config_nomad.yaml
```

## Project layout

```
src/chaotic/
├── cli.py            # argument parsing, env fallbacks, exit codes
├── runner.py         # one-shot and periodic execution
├── config.py         # loading and validating a chaos plan
├── excludes.py       # "do not touch anything right now" windows
├── factory.py        # config kind -> provider class
├── errors.py         # ChaoticError and friends
├── log.py            # logging setup
└── providers/
    ├── base.py       # Chaotic, RestartChaotic, Target
    └── <provider>.py # one module per API
tests/                # mirrors the layout above
```

## Adding a provider

Most providers do the same thing: pick a random machine, stop it, wait, start it
again. That experiment lives in `RestartChaotic`, so a new provider only answers
three questions:

```python
from functools import cached_property
from typing import Sequence

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target


class ExampleChaotic(RestartChaotic):
    """Stop and start a random Example Cloud server."""

    target_noun = "server"  # only used in log messages

    @cached_property
    def client(self) -> ExampleSDK:
        # Built lazily, so importing the module never touches the network
        # and never requires credentials.
        return ExampleSDK(token=os.getenv("EXAMPLE_API_TOKEN", ""))

    def list_targets(self) -> Sequence[Target]:
        tag = self.configs.get("tag")
        log.info("Querying with tag: %s", tag)
        return [Target(id=s.id, name=s.name, raw=s) for s in self.client.servers(tag=tag)]

    def stop(self, target: Target) -> None:
        self.client.stop(target.id)

    def start(self, target: Target) -> None:
        self.client.start(target.id)
```

Override `skip_reason()` to veto a target after it has been chosen — Proxmox uses
it for `min_uptime`. Providers with a genuinely different experiment subclass
`Chaotic` directly and implement `action()`; `NomadChaotic` is the example.

Then:

1. Register the class in `PROVIDERS` in `src/chaotic/factory.py`.
2. Add an `examples/config_<kind>.yaml`.
3. Add `docs/configs/<kind>.md` and list it in the `nav` of `mkdocs.yml`.
4. Add tests. `tests/conftest.py` provides `make_provider()`, which swaps the
   lazy `client` for a fake, and the `no_sleep` fixture.

`tests/test_package.py` fails if a provider has no example config, and
`tests/test_factory.py` fails if the registry and the documented kinds drift
apart.

## Conventions

* **No import side effects.** Modules must not read credentials, open sockets or
  configure logging at import time. Credentials are read when the API client is
  first used, which is what makes the providers testable.
* **Lazy log formatting.** Use `log.info("Selected %s", name)`, not an f-string —
  the JSON formatter and the linter both expect it.
* **Errors.** Raise a `ChaoticError` subclass for anything an operator can fix.
  The CLI logs those as a single line and exits 1; anything else gets a
  traceback.
