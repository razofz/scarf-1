import pytest
import zarr

from ..assay import Assay
from ..metadata import MetaData
from . import full_path, remove


@pytest.fixture(scope="session")
def dummy_assay():
    import tarfile

    fn = full_path("1K_pbmc_citeseq.zarr.tar.gz")
    out_fn = fn.replace(".tar.gz", "")
    remove(out_fn)
    tar = tarfile.open(fn, "r:gz")
    tar.extractall(out_fn)
    z = zarr.open(out_fn)
    metadata = MetaData(z.cellData)
    assay = Assay(
        z=z,
        name="RNA",
        cell_data=metadata,
        nthreads=1)
    yield assay
    remove(out_fn)
