from . import full_path, remove


def test_downloader():
    from ..downloader import osfd, OSFdownloader
    import pytest

    if osfd is None:
        osfd = OSFdownloader("zeupv")
    # Making sure that there are at least 15 datasets in the list
    assert len(osfd.datasets) > 15
    with pytest.raises(KeyError):
        osfd.get_dataset_file_ids("non_existing_name")


def test_show_available_datasets():
    from ..downloader import show_available_datasets

    show_available_datasets()


def test_fetch_dataset(bastidas_ponce_data):
    # TODO: check if correct file was downloaded.
    pass


def test_downloader_as_zarr():
    from ..downloader import fetch_dataset

    # TODO: check if only the zarr file was downloaded

    sample = "tenx_5K_pbmc_rnaseq"
    fetch_dataset(sample, as_zarr=True, save_path=full_path(None))
    remove(full_path(sample))

def test_non_existing_dataset():
    from ..downloader import OSFdownloader
    import pytest

    with pytest.raises(KeyError):
        OSFdownloader("non_existing_dataset")
