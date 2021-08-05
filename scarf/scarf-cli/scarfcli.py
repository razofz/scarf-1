import click
import scarf
import pandas as pd
import os

# functionality to support:
# - fetch_dataset (INPUT: what dataset to fetch)
# - Cr*Reader (maybe just readers in general. can it be auto-id'd?) (INPUT)
# - in vignette reader features are inspected, maybe just print them
# - verbose / non-verbose option
# - Writer(s) (user should specify OUTPUT Zarr file (where results from
# DataStore also will be saved. Right?))
# - make a DataStore
# - how to deal with plots?
# - ds.mark_hvgs
# - ds.make_graph
# - ds.run_umap
# - export ds.plot_layout?
#   - for umap
#   - and tsne?
# - ds.run_leiden_clustering
# - ds.run_marker_search
# - marker heatmap?
# - OUTPUT markers
# -
# -
# - arguments (compulsory to provide):
#   - INPUT: what dataset to fetch
#   - OUTPUT: output Zarr file
#   - OUTPUT: marker csv file
#   - OUTPUT: alternatively, just specify a directory name and all output ends
#   up there. That sounds good and easy.
#   -
#   -
# -
# - options:
#   - nthreads
#   - min_features_per_cell
#   - chunk size
#   - file_type for Reader, e. g. 'rna'
#   - autofilter cells as default I guess, but maybe should expose limits as
#   options/flags
#   - k for make_graph
#   - dims for make_graph / lindimred
#   - clustering resolution
#   - marker threshold
#   -


class Scarf_cli(object):
    #     def __init__(self, dataset='tenx_5K_pbmc_rnaseq',
    #                  output_dir='./basic-scRNA-Seq'):
    def __init__(self, dataset, output_dir, nthreads):
        self.dataset = dataset
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.datastore = None
        if nthreads is not None:
            self.nthreads = nthreads
        else:
            self.nthreads = 4

    def __str__(self):
        return f"Dataset: {self.dataset}, Output dir: {self.output_dir}"

    def download_dataset(self):
        click.echo(
            f"> Downloading dataset " + click.style(f"{self.dataset}", bold=1) + ".."
        )
        scarf.fetch_dataset(self.dataset, save_path=self.output_dir)

    def read_data(self):
        reader = scarf.CrH5Reader(
            f"{self.output_dir}/{self.dataset}/data.h5", file_type="rna"
        )
        zarr_fn = f"{self.output_dir}/data.zarr"
        click.echo(
            f"> Creating zarr file from dataset, at "
            + click.style(click.format_filename(f"{zarr_fn}"), bold=1)
            + ".."
        )
        writer = scarf.CrToZarr(reader, zarr_fn=zarr_fn, chunk_size=(2000, 1000))
        writer.dump(batch_size=1000)
        self.ds = scarf.DataStore(
            zarr_fn, nthreads=self.nthreads, min_features_per_cell=10
        )

    def filter_data(self, attrs=None, highs=None, lows=None):
        click.echo("> Filtering data..")
        if attrs == None:
            self.ds.auto_filter_cells(show_qc_plots=False)

    #         ds.filter_cells(attrs=['RNA_nCounts', 'RNA_nFeatures', 'RNA_percentMito'],
    #                 highs=[15000, 4000, 15], lows=[1000, 500, 0])

    def mark_hvgs(self):
        click.echo("> Finding highly variable genes..")
        self.ds.mark_hvgs()

    def construct_graph(self):
        click.echo("> Constructing graph..")
        self.ds.make_graph(feat_key="hvgs")
        self.ds.run_umap()
        self.ds.run_clustering(n_clusters=12)
        self.ds.run_marker_search(group_key="RNA_cluster")

    def save_data(self):
        click.echo("> Saving data..")
        self.ds.export_markers_to_csv(
            group_key="RNA_cluster", csv_filename=f"{self.output_dir}/markers.csv"
        )

    def run_pipeline(self):
        self.download_dataset()
        self.read_data()
        self.filter_data()
        self.mark_hvgs()
        self.construct_graph()
        self.save_data()


def print_datasets(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    scarf.downloader.show_available_datasets()
    ctx.exit()


@click.group()
@click.option(
    "--show-datasets",
    is_flag=True,
    callback=print_datasets,
    expose_value=False,
    is_eager=True,
    help="Show the prepared datasets available for download.",
)
@click.version_option()
# can add scarf.__version__() here later
# right now only works when pip installed
@click.pass_context
def cli(ctx):
    pass
    # could just put everything into here. In the basic case, i. e. running an
    # automated analysis of a given dataset, we really don't need all fancy
    # functionality of click, we can make it easier for ourselves.
    # For doing one's own dataset, where one wants to decide on filter
    # thresholds etc, it makes more sense to split up the functionality. But as
    # a first step, mayhaps a PoC automated pipeline is okay.


@cli.command()
@click.option("--dataset", default="tenx_5K_pbmc_rnaseq", type=str, show_default=True)
@click.option("-o", "--outputdir", default="./basic-scRNA-Seq", show_default=True)
# filenames should be handled in a specific way according to click docs
@click.option("-j", "--nthreads", default=4, required=False)
@click.pass_context
def run_pipeline(ctx, dataset, outputdir, nthreads):
    """Run the whole pipeline, as automated as possible."""
    ctx.obj = Scarf_cli(dataset, outputdir, nthreads)
    click.echo(ctx.obj)
    ctx.obj.run_pipeline()


if __name__ == "__main__":
    cli()

# can enable auto-completion, unfortunately with some effort from the user: https://click.palletsprojects.com/en/8.0.x/shell-completion/
