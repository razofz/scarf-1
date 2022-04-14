from . import full_path


def test_set_verbosity():
    import pytest

    from ..utils import set_verbosity

    with pytest.raises(ValueError):
        set_verbosity(level=None)
    with pytest.raises(ValueError):
        set_verbosity(level="FAULTY_VALUE")
    set_verbosity(level="WARNING")
    # Not sure what to otherwise test for here. Could e.g. not find a way in
    # loguru to show already existing loggers. - RO


def test_system_call():
    from ..utils import system_call

    system_call("ls")


def test_rolling_window():
    # seems like we need to disable numba for this test to count towards
    # coverage: https://github.com/vc1492a/PyNomaly/issues/32
    # https://stackoverflow.com/questions/26875191/analyzing-coverage-of-numba-wrapped-functions
    # Disable numba with `export NUMBA_DISABLE_JIT=1`.
    # However, this makes `test_run_pseudotime_aggregation` fail..
    # https://github.com/numba/numba/issues/4268
    from ..utils import rolling_window
    import numpy as np

    assert (rolling_window(np.ones([10, 10]), 10) == np.ones([10, 10])).all()


def test_tqdmbar():
    from ..utils import tqdmbar, tqdm_params
    if "disable" in tqdm_params:
        del tqdm_params["disable"]
    tqdmbar(ncols=499)
