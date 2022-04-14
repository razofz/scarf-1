import pytest
from . import full_path, remove
import numpy as np


def test_norm_dummy():
    import dask.array as daskarr
    from ..assay import norm_dummy

    counts = daskarr.from_array(np.array([[1, 2, 3], [4, 5, 6]]))
    assert (norm_dummy(..., counts=counts) == counts).compute().all()


def test_norm_clr_returns_daskarr(dummy_assay):
    import dask
    from ..assay import norm_clr

    assert isinstance(
        norm_clr(dummy_assay, counts=dummy_assay.rawData), dask.array.core.Array
    )


def test_norm_clr_consistent_calculation(dummy_assay):
    import dask
    from ..assay import norm_clr

    assert (
        round(
            norm_clr(dummy_assay, counts=dummy_assay.rawData).compute().max(), 5
        )
        == 5.19256
    )
    assert (
        round(
            norm_clr(dummy_assay, counts=dummy_assay.rawData).compute().mean(),
            5,
        )
        == 0.04511
    )


def test_normed(dummy_assay):
    from ..assay import norm_dummy

    dummy_assay.normMethod = norm_dummy
    dummy_assay.cells.insert(
        "RNA_nCounts",
        values=np.array([x for x in range(1, dummy_assay.cells.N + 1)]),
        overwrite=True,
    )
    # these two tests should probably be for
    # metadata active_index instead
    assert (
        np.array([x for x in range(0, dummy_assay.cells.N)])
        == dummy_assay.cells.active_index("I")
    ).all()
    assert (
        np.array([x for x in range(0, dummy_assay.feats.N)])
        == dummy_assay.feats.active_index("I")
    ).all()
    assert (
        dummy_assay.rawData == dummy_assay.normed(cell_idx=None, feat_idx=None)
    ).all()
