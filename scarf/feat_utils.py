import pandas as pd
import numpy as np
from typing import List

__all__ = ['fit_lowess', 'score_features']


def fit_lowess(a, b, n_bins: int, lowess_frac: float) -> np.ndarray:
    """

    Args:
        a:
        b:
        n_bins:
        lowess_frac:

    Returns:

    """
    from statsmodels.nonparametric.smoothers_lowess import lowess

    stats = pd.DataFrame({'a': a, 'b': b}).apply(np.log)
    bin_edges = np.histogram(stats.a, bins=n_bins)[1]
    bin_edges[-1] += 0.1  # For including last gene
    bin_idx = []
    for i in range(n_bins):
        idx = pd.Series((stats.a >= bin_edges[i]) & (stats.a < bin_edges[i + 1]))
        if sum(idx) > 0:
            bin_idx.append(list(idx[idx].index))
    bin_vals = []
    for idx in bin_idx:
        temp_stat = stats.reindex(idx)
        temp_gene = temp_stat.idxmin().b
        bin_vals.append(
            [temp_stat.b[temp_gene], temp_stat.a[temp_gene]])
    bin_vals = np.array(bin_vals).T
    bin_cor_fac = lowess(bin_vals[0], bin_vals[1], return_sorted=False,
                         frac=lowess_frac, it=100).T
    fixed_var = {}
    for bcf, indices in zip(bin_cor_fac, bin_idx):
        for idx in indices:
            fixed_var[idx] = np.e ** (stats.b[idx] - bcf)
    return np.array([fixed_var[x] for x in range(len(a))])


def score_features(assay, feature_list: List[str], ctrl_size: int = 50,
                   n_bins: int = 25, rand_seed: int = 0) -> np.ndarray:
    """
    Score a set of genes [Satija15]_.
    The score is the average expression of a set of genes subtracted with the
    average expression of a reference set of genes. The reference set is
    randomly sampled from the `gene_pool` for each binned expression value.

    This reproduces the approach in Seurat [Satija15]_ and has been implemented
    for Scanpy by Davide Cittaro.

    This function is adapted from Scanpy's `score_genes`.

    Args:
        assay:
        feature_list:
        ctrl_size:
        n_bins:
        rand_seed:

    Returns:

    """
    def _name_to_ids(i):
        x = assay.feats.table.reindex(assay.feats.get_idx_by_names(i))
        x = x[x.I]
        return x.ids.values

    def _calc_mean(i):
        idx = sorted(assay.feats.get_idx_by_ids(i))
        return assay.normed(feat_idx=idx).mean(axis=1).compute()

    feature_list = set(_name_to_ids(feature_list))
    obs_avg = pd.Series(assay.z.summary_stats_I.avg[:], index=assay.feats.fetch('ids'))
    n_items = int(np.round(len(obs_avg) / (n_bins - 1)))

    # Made following more linter friendly
    # obs_cut = obs_avg.rank(method='min') // n_items
    obs_cut: pd.Series = obs_avg.rank(method='min').divide(n_items).astype(int)

    control_genes = set()
    for cut in np.unique(obs_cut.loc[feature_list]):
        # Replaced np.random.shuffle with pandas' sample method
        r_genes = obs_cut[obs_cut == cut].sample(n=ctrl_size, random_state=rand_seed)
        control_genes.update(set(r_genes.index))
    control_genes = control_genes - feature_list
    return _calc_mean(list(feature_list)) - _calc_mean(list(control_genes))
