---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.4
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

## Merging datasets and partial training

This vignette demonstrates how to merge datasets, which are present in different zarr files. The vignette will also demonstrate the steps for performing partial training. Partial PCA training is a lightweight alternative to perform batch effect correction, that often helps obtain a well-integrated embedding and clustering.

```{code-cell} ipython3
%load_ext autotime

import scarf
scarf.__version__
```

---
### 1) Fetch datasets in Zarr format

Here we will use the same datasets are we use in the ['data projection'](https://scarf.readthedocs.io/en/latest/vignettes/data_projection.html) vignette. We download the files in zarr format.

```{code-cell} ipython3
scarf.fetch_dataset(
    dataset_name='kang_15K_pbmc_rnaseq',
    save_path='scarf_datasets',
    as_zarr=True
)

scarf.fetch_dataset(
    dataset_name='kang_14K_ifnb-pbmc_rnaseq', 
    save_path='scarf_datasets',
    as_zarr=True
)
```

The Zarr files need to be loaded as a DataStore before they can be merged:

```{code-cell} ipython3
ds_ctrl = scarf.DataStore(
    'scarf_datasets/kang_15K_pbmc_rnaseq/data.zarr/',
    nthreads=4
)

ds_ctrl
```

```{code-cell} ipython3
ds_stim = scarf.DataStore(
    'scarf_datasets/kang_14K_ifnb-pbmc_rnaseq/data.zarr',
    nthreads=4
)

ds_stim
```

---
### 2) Merging datasets

The merging step will make sure that the features are in the same order as in the merged file. The merged data will be dumped into a new Zarr file. `ZarrMerge` class allows merging multiple samples at the same time. Though only one kind of assays can be added at a time, other modalities for the same cells can be added at a later point. 

```{code-cell} ipython3
#Can be used to merge multiple assays
scarf.ZarrMerge(
    # Path where merged Zarr files will be saved
    zarr_path='scarf_datasets/kang_merged_pbmc_rnaseq.zarr',  
    
    # assays to be merged
    assays=[ds_ctrl.RNA, ds_stim.RNA],
    
    # these names will be preprended to the cell ids with '__' delimiter
    names=['ctrl', 'stim'],
    
    # Name of the merged assay. `overwrite` will remove an existing Zarr file.
    merge_assay_name='RNA',
    overwrite=True
).dump()
```

Load the merged Zarr file as a DataStore:

```{code-cell} ipython3
ds = scarf.DataStore(
    'scarf_datasets/kang_merged_pbmc_rnaseq.zarr',
    nthreads=4
)
```

So now we print the merged datastore. The merging removed all the precalculated data. Even the information on which cells were filtered out is lost in the process. This is done deliberately, to allow users to start fresh with the merged dataset.

```{code-cell} ipython3
ds
```

If we have a look at the cell attributes table, we can clearly see the that the sample identity is shown in the `ids` column, prepended to the barcode.

```{code-cell} ipython3
ds.cells.head()
```

It can be a good idea to keep track of the cells from different samples, we can fetch out the dataset id from cell-barcodes and add them separately in a new column (this step might get automated in the future).

```{code-cell} ipython3
ds.cells.insert(
    column_name='sample_id',
    values=[x.split('__')[0] for x in ds.cells.fetch_all('ids')],
    overwrite=True
)
```

Rather than performing a fresh round of annotation, we will also import the cluster labels from the unmerged datasets. This help us at later steps to evaluate our results.

```{code-cell} ipython3
ctrl_labels = list(ds_ctrl.cells.fetch_all('cluster_labels'))
stim_labels = list(ds_stim.cells.fetch_all('cluster_labels'))

ds.cells.insert(
    column_name='imported_labels',
    values=ctrl_labels + stim_labels,
    overwrite=True
)
```

As well as re-using annotations, we import the information about which cells where kept and which ones where filtered out.

```{code-cell} ipython3
ctrl_valid_cells = list(ds_ctrl.cells.fetch_all('I'))
stim_valid_cells = list(ds_stim.cells.fetch_all('I'))

ds.cells.update_key(
    values=ctrl_valid_cells + stim_valid_cells,
    key='I'
)
```

Now we can check the number of cells from each of the samples:

```{code-cell} ipython3
ds.cells.to_pandas_dataframe(
    ['sample_id'],
    key='I'
)['sample_id'].value_counts()
```

---
### 3) Naive analysis of merged datasets

By naive, we mean that we make no attempt to remove/account for the latent factors that might contribute to batch effect or treatment-specific effect.
It is usually a good idea to perform a 'naive' pipeline to get an idea about the degree of batch effects.

+++

We start with detecting the highly variable genes:

```{code-cell} ipython3
ds.mark_hvgs(
    min_cells=10,
    top_n=2000,
    min_mean=-3, 
    max_mean=2,
    max_var=6
)
```

Next, we create a graph of cells in a standard way.

```{code-cell} ipython3
ds.make_graph(
    feat_key='hvgs',
    k=21, 
    dims=25,
    n_centroids=100
)
```

Calculating UMAP embedding of cells:

```{code-cell} ipython3
ds.run_umap(
    n_epochs=250, 
    spread=5,
    min_dist=1,
    parallel=True
)
```

```{code-cell} ipython3
ds.cells.head()
```

Visualization of cells from the two samples in the 2D UMAP space:

```{code-cell} ipython3
ds.plot_layout(
    layout_key='RNA_UMAP',
    color_by='sample_id',
    cmap='RdBu', 
    legend_ondata=False
)
```

Visualization of cluster labels in the 2D UMAP space:

```{code-cell} ipython3
ds.plot_layout(
    layout_key='RNA_UMAP', 
    color_by='imported_labels',
    legend_ondata=False
)
```

---
### 4) Partial PCA training to reduce batch effects

The plots above clearly show that the cells from the two samples are distinct on the UMAP space and have not integrated. This clearly indicates a treatment-specific or simply a batch effect between the cells from the two samples. Another interesting pattern in the UMAP plot above is the 'mirror effect', i.e. the equivalent clusters from the two samples look like mirror images. This is often seen in the datasets where the heterogenity/cell population composition is not strongly affected by the treatment.

We will now attempt to integrate the cells from the two samples so that we obtain same cell types that do not form separate clusters. One can do this by training the PCA on cells from only one of the samples. Training PCA on cells from only one of the samples will diminish the contribution of genes differentially expressed between the two samples.

+++

First, we need to create a boolean column in the cell attribute table. This column will indicate whether a cell belongs to one of the samples. Here we will create a new column `is_ctrl` and mark the values as True when a cell belongs to the `ctrl` sample.

```{code-cell} ipython3
ds.cells.insert(
    column_name=f'is_ctrl',
    values=(ds.cells.fetch_all('sample_id') == 'ctrl'),
    overwrite=True
)
```

The next step is to perform the partial PCA training. PCA is trained during the graph creation step. We will now use `pca_cell_key` parameter and set it to `is_ctrl` so that only 'ctrl' cells are used for PCA training.

```{code-cell} ipython3
ds.make_graph(
    feat_key='hvgs',
    k=21, 
    dims=25,
    n_centroids=100,
    pca_cell_key='is_ctrl'
)
```

We run UMAP as usual, but the UMAP embeddings are saved in a new cell attribute column so as to not overwrite the previous UMAP values. The new column will be called `RNA_pUMAP`; 'RNA' is automatically prepend because the assay name is `RNA`

```{code-cell} ipython3
ds.run_umap(
    n_epochs=250, 
    spread=5,
    min_dist=1,
    parallel=True,
    label='pUMAP'
)
```

Visualize the new UMAP

```{code-cell} ipython3
ds.plot_layout(
    layout_key='RNA_pUMAP',
    color_by='sample_id',
    cmap='RdBu',
    legend_ondata=False
)
```

Visualization of cluster labels in the new UMAP space shows that the cells from the same cell-type do not split into separate clusters like they did before.

```{code-cell} ipython3
ds.plot_layout(
    layout_key='RNA_pUMAP',
    color_by='imported_labels',
    legend_ondata=False
)
```

---
That is all for this vignette.
