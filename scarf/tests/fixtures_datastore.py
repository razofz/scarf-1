import pytest
from . import full_path, remove
import numpy as np
import pandas as pd


@pytest.fixture(scope="session")
def toy_crdir_writer(toy_crdir_reader):
    from ..writers import CrToZarr

    out_fn = full_path("toy_crdir.zarr")

    writer = CrToZarr(toy_crdir_reader, out_fn)
    writer.dump()
    yield out_fn
    remove(out_fn)


@pytest.fixture(scope="session")
def toy_crdir_ds(toy_crdir_writer):
    from ..datastore import DataStore

    yield DataStore(toy_crdir_writer, default_assay="RNA")


@pytest.fixture(scope="session")
def datastore():
    import tarfile

    from ..datastore import DataStore

    fn = full_path("1K_pbmc_citeseq.zarr.tar.gz")
    out_fn = fn.replace(".tar.gz", "")
    remove(out_fn)
    tar = tarfile.open(fn, "r:gz")
    tar.extractall(out_fn)
    yield DataStore(out_fn, default_assay="RNA")
    remove(out_fn)


@pytest.fixture
def datastore_ephemeral():
    import tarfile

    from ..datastore import DataStore

    fn = full_path("1K_pbmc_citeseq.zarr.tar.gz")
    out_fn = fn.replace(".tar.gz", "")
    remove(out_fn)
    tar = tarfile.open(fn, "r:gz")
    tar.extractall(out_fn)
    yield DataStore(out_fn, default_assay="RNA")
    remove(out_fn)


@pytest.fixture(scope="class")
def auto_filter_cells(datastore):
    datastore.auto_filter_cells(show_qc_plots=False)


@pytest.fixture(scope="class")
def mark_hvgs(auto_filter_cells, datastore):
    datastore.mark_hvgs(top_n=100, show_plot=False)


@pytest.fixture(scope="class")
def make_graph(mark_hvgs, datastore):
    datastore.make_graph(feat_key="hvgs")
    graph_loc = datastore._get_latest_graph_loc(
        from_assay="RNA", cell_key="I", feat_key="hvgs"
    )
    yield graph_loc.rsplit("/", 1)[0]


@pytest.fixture(scope="class")
def leiden_clustering(make_graph, datastore):
    datastore.run_leiden_clustering()
    yield datastore.cells.fetch("RNA_leiden_cluster")


@pytest.fixture(scope="class")
def paris_clustering(make_graph, datastore):
    datastore.run_clustering(n_clusters=10)
    yield datastore.cells.fetch("RNA_cluster")


@pytest.fixture(scope="class")
def paris_clustering_balanced(make_graph, datastore):
    datastore.run_clustering(
        balanced_cut=True, max_size=100, min_size=10, label="balanced_clusters"
    )
    yield datastore.cells.fetch("RNA_balanced_clusters")


@pytest.fixture(scope="class")
def umap(make_graph, datastore):
    datastore.run_umap(n_epochs=50)
    yield np.array(
        [datastore.cells.fetch("RNA_UMAP1"), datastore.cells.fetch("RNA_UMAP2")]
    ).T


@pytest.fixture(scope="class")
def tsne(make_graph, datastore):
    datastore.run_tsne()
    yield np.array(
        [datastore.cells.fetch("RNA_tSNE1"), datastore.cells.fetch("RNA_tSNE2")]
    ).T


@pytest.fixture(scope="class")
def marker_search(datastore):
    # Testing this with Paris clusters rather then Leiden clusters because of reproducibility.
    datastore.run_marker_search(group_key="RNA_cluster")


@pytest.fixture(scope="class")
def pseudotime_scoring(datastore, leiden_clustering):
    datastore.run_pseudotime_scoring(
        source_sink_key="RNA_leiden_cluster", sources=[6], sinks=[3]
    )
    yield datastore.cells.fetch("RNA_pseudotime")


@pytest.fixture(scope="class")
def pseudotime_markers(datastore, pseudotime_scoring):
    datastore.run_pseudotime_marker_search(pseudotime_key="RNA_pseudotime")
    df = datastore.RNA.feats.to_pandas_dataframe(
        ["names", "I__RNA_pseudotime__r"], key="I"
    )
    yield df


@pytest.fixture(scope="class")
def pseudotime_aggregation(datastore, pseudotime_scoring):
    datastore.run_pseudotime_aggregation(
        pseudotime_key="RNA_pseudotime",
        cluster_label="pseudotime_clusters",
        n_clusters=15,
        window_size=50,
        chunk_size=10,
    )


@pytest.fixture(scope="class")
def grouped_assay(datastore, pseudotime_aggregation):
    datastore.add_grouped_assay(
        group_key="pseudotime_clusters", assay_label="PTIME_MODULES"
    )


@pytest.fixture(scope="class")
def run_mapping(make_graph, datastore):
    datastore.run_mapping(
        target_assay=datastore.RNA,
        target_name="selfmap",
        target_feat_key="hvgs_self",
        save_k=3,
    )


@pytest.fixture(scope="class")
def run_mapping_coral(make_graph, datastore):
    datastore.run_mapping(
        target_assay=datastore.RNA,
        target_name="selfmap_coral",
        target_feat_key="hvgs_self2",
        save_k=3,
        run_coral=True,
    )


@pytest.fixture(scope="class")
def run_unified_umap(run_mapping, datastore):
    datastore.run_unified_umap(target_names=["selfmap"])


@pytest.fixture(scope="class")
def cell_cycle_scoring(datastore):
    datastore.run_cell_cycle_scoring()
    return datastore.cells.fetch("RNA_cell_cycle_phase")


@pytest.fixture(scope="class")
def topacedo_sampler(paris_clustering, datastore):
    datastore.run_topacedo_sampler(cluster_key="RNA_cluster")
    return datastore.cells.fetch("RNA_sketched")


@pytest.fixture(scope="class")
def cell_attrs():
    return pd.read_csv(full_path("cell_attributes.csv"), index_col=0)


@pytest.fixture(scope="session")
def atac_datastore():
    from ..datastore import DataStore
    import tarfile

    fn = full_path("500_pbmc_atac.zarr.tar.gz")
    out_fn = fn.replace(".tar.gz", "")
    remove(out_fn)
    tar = tarfile.open(fn, "r:gz")
    tar.extractall(out_fn)
    yield DataStore(out_fn)
    remove(out_fn)


@pytest.fixture(scope="class")
def mark_prevalent_peaks(atac_datastore):
    atac_datastore.mark_prevalent_peaks(top_n=5000)


@pytest.fixture(scope="class")
def make_atac_graph(mark_prevalent_peaks, atac_datastore):
    atac_datastore.make_graph(feat_key="prevalent_peaks")
    graph_loc = atac_datastore._get_latest_graph_loc(
        from_assay="ATAC", cell_key="I", feat_key="prevalent_peaks"
    )
    yield graph_loc.rsplit("/", 1)[0]
