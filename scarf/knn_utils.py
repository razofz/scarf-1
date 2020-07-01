import numpy as np
from umap.umap_ import smooth_knn_dist, compute_membership_strengths
from .writers import create_zarr_dataset
from .ann import AnnStream
from . import threadpool_limits
from tqdm import tqdm

__all__ = ['make_knn_graph', 'export_knn_to_mtx']


def make_knn_graph(ann_obj: AnnStream, chunk_size: int, store, nthreads: int,
                  lc: float, bw: float, save_raw_dists: bool):
    # bandwidth: Higher value will push the mean of distribution of graph edge weights towards right
    # local_connectivity: Higher values will create push distribution of edge weights towards terminal values (binary
    # like) Lower values will accumulate edge weights around the mean produced by bandwidth

    n_cells, n_neighbors = ann_obj.nCells, ann_obj.k
    z_knn = create_zarr_dataset(store, 'indices', (chunk_size,), 'u8',
                                (n_cells, n_neighbors))
    z_dist = create_zarr_dataset(store, 'distances', (chunk_size,), 'f8',
                                    (n_cells, n_neighbors))
    zge = create_zarr_dataset(store, 'edges', (chunk_size,), ('u8', 'u8'),
                              (n_cells * n_neighbors, 2))
    zgw = create_zarr_dataset(store, 'weights', (chunk_size,), 'f8',
                              (n_cells * n_neighbors,))
    last_row = 0
    val_counts = 0
    nsample_start = 0
    with threadpool_limits(limits=nthreads):
        for i in ann_obj.iter_blocks(msg='Saving KNN graph'):
            nsample_end = nsample_start + i.shape[0]
            ki, kv = ann_obj.transform_ann(ann_obj.reducer(i), k=n_neighbors,
                                           self_indices=np.arange(nsample_start, nsample_end))
            kv = kv.astype(np.float32, order='C')
            sigmas, rhos = smooth_knn_dist(kv, k=n_neighbors,
                                           local_connectivity=lc, bandwidth=bw)
            rows, cols, vals = compute_membership_strengths(ki, kv, sigmas, rhos)
            rows = rows + last_row
            start = val_counts
            end = val_counts + len(rows)
            last_row = rows[-1] + 1
            val_counts += len(rows)
            if save_raw_dists:
                z_knn[nsample_start:nsample_end, :] = ki
                z_dist[nsample_start:nsample_end, :] = kv
            zge[start:end, 0] = rows
            zge[start:end, 1] = cols
            zgw[start:end] = vals
            nsample_start = nsample_end
    return None


def export_knn_to_mtx(mtx: str, store) -> None:
    with open(mtx, 'w') as h:
        h.write("%%MatrixMarket matrix coordinate real general\n% Generated by Scarf\n")
        s0, s1 = store.attrs['n_cells'], store.attrs['k']
        h.write(f"{s0} {s0} {s0 * s1}\n")
        e = store.edges[:] + 1
        w = store.weights[:]
        temp = []
        for i in tqdm(range(0, e.shape[0], s1), desc='Saving KNN matrix in MTX format'):
            idx = np.argsort(e[i:i + s1][:, 1])
            ww = w[i:i + s1][idx]
            ww = ww / ww.sum()
            for j, k in zip(e[i:i + s1][idx], ww):
                temp.append(f'{j[1]} {j[0]}  {k}\n')
            if i % 1000 == 0:
                h.write(''.join(temp))
                temp = []
        if len(temp) > 0:
            h.write(''.join(temp))
    return None
