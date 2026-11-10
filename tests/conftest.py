import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automation"))

import lab  # noqa: E402


def wait_until(fn, timeout: float = 60, interval: float = 3):
    """Reintenta fn() hasta que devuelva algo verdadero o se agote el tiempo."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = fn()
            if last:
                return last
        except Exception as exc:  # el nodo aun puede estar arrancando
            last = exc
        time.sleep(interval)
    return last


@pytest.fixture(scope="session")
def lab_mod():
    res = lab.run("p1", ["true"])
    if res.returncode != 0:
        pytest.exit("El laboratorio no esta desplegado (make deploy).", returncode=2)
    return lab
