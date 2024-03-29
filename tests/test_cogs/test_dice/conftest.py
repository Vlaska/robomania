from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def set_seed() -> None:
    np.random.seed(0)
