import click
import scarf

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
    def __init__(self, dataset='tenx_5K_pbmc_rnaseq',
                 output_dir='./basic-scRNA-Seq'):
        self.dataset = dataset
        self.output_dir = output_dir
        self.datastore = None
        if nthreads not None:
            self.nthreads=nthreads
        else:
            self.nthreads=4

    def read_data():
        reader = scarf.CrH5Reader(self.dataset)
        zarr_fn= self.output_dir + '/' +  self.dataset +  '.zarr',
        writer = scarf.CrToZarr(reader,
                zarr_fn= zarr_fn,
                chunk_size=(2000, 1000))
        writer.dump(batch_size=1000)
        self.ds = scarf.DataStore(zarr_fn, nthreads=self.nthreads,
                min_features_per_cell=10)

    def filter_data(attrs, highs, lows):
        if attrs = None:
            self.ds.auto_filter_cells(show_qc_plots=False)
        ds.filter_cells(attrs=['RNA_nCounts', 'RNA_nFeatures', 'RNA_percentMito'],
                highs=[15000, 4000, 15], lows=[1000, 500, 0])

@click.group()
@click.option('--dataset', default='tenx_5K_pbmc_rnaseq')
@click.option('--outputdir', default='./basic-scRNA-Seq')
@click.pass_context
def cli(ctx, dataset, outputdir):
    ctx.obj = Scarf_cli(dataset, outputdir)

@cli.command()
# @click.pass_obj
def show_datasets():
    datasets = scarf.downloader.show_available_datasets()
    click.echo(datasets)
#     click.echo(obj)

if __name__ == "__main__":
    cli()

