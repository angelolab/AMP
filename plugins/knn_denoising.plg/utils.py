import numpy as np

from scipy.stats import gamma
from scipy.optimize import fsolve
from scipy.special import digamma
from scipy.special import gamma as gamma_func

def _alpha_eqn(ahat: float, C: float) -> float:
    return np.log(ahat) - digamma(ahat) - C

def _calc_q(x, Ts, ws, alphas, betas):
    param_terms = alphas * np.log(betas) - np.log(gamma_func(alphas)) + np.log(ws)
    combined_terms = (
        (alphas[:, np.newaxis] - 1) * np.log([x,]*alphas.shape[0])
        - betas[:, np.newaxis] * np.array([x, ]* alphas.shape[0])
    )
    return np.sum(Ts * (param_terms[:, np.newaxis] + combined_terms))

def _gamma_mixture(x, n_dists, max_iter, init_index, tol):

    # for a gamma distribution, alpha = mean**2 / var, beta = mean / var
    ws, alphas, betas = (np.zeros(n_dists), np.zeros(n_dists), np.zeros(n_dists))
    dist_pdfs = np.zeros((n_dists, x.shape[0]))
    for i in range(n_dists):
        ws[i] = np.mean(init_index == i)
        alphas[i] = (np.mean(x[init_index == i]) ** 2) / np.var(x[init_index == i])
        betas[i] = np.mean(x[init_index == i]) / np.var(x[init_index == i])
        dist_pdfs[i] = gamma.pdf(x, alphas[i], scale = 1 / betas[i])

    total_dist = np.dot(dist_pdfs.T, ws)

    z_cond_dists = (ws[:, np.newaxis] * dist_pdfs) / total_dist

    while range(max_iter):

        sum_Ts = np.sum(z_cond_dists, axis=1)
        sum_Txs = np.dot(z_cond_dists, x)
        sum_Tlogxs = np.dot(z_cond_dists, np.log(x))

        alpha_eq_consts = np.log(sum_Txs / sum_Ts) - (sum_Tlogxs / sum_Ts)

        # compute argmax's
        a_hats = np.array([
            fsolve(_alpha_eqn, alphas[i], args=(alpha_eq_consts[i]))[0]
            for i in range(n_dists)
        ])
        b_hats = a_hats * sum_Ts / sum_Txs
        w_hats = sum_Ts / x.shape[0]

        # get next iter distributions
        dist_pdfs_next = np.array([gamma.pdf(x, a_hats[i], scale = 1 / b_hats[i]) for i in range(n_dists)])
        total_dist_next = np.dot(dist_pdfs_next.T, w_hats)
        z_cond_dists_next = (w_hats[:, np.newaxis] * dist_pdfs_next) / total_dist_next

        # compute delta_q
        delta_q = (
            _calc_q(x, z_cond_dists_next, w_hats, a_hats, b_hats)
            - _calc_q(x, z_cond_dists, ws, alphas, betas)
        )
        
        # update params and distributions
        ws, alphas, betas = (w_hats, a_hats, b_hats)
        dist_pdfs = dist_pdfs_next
        total_dist = total_dist_next
        z_cond_dists = z_cond_dists_next

        if np.abs(delta_q) <= tol:
            break

    return ws, alphas, betas

_INIT_KNN_THRESH = 6

def optimize_threshold(knn_dists):
    # approximate initial distribution assignments
    assignment_guess = np.zeros_like(knn_dists)
    assignment_guess[knn_dists > _INIT_KNN_THRESH] = 1

    w, alpha, beta = _gamma_mixture(knn_dists, 2, 500, assignment_guess, 1e-3)

    means = np.sort(alpha / beta)
    x = np.linspace(means[0], means[1], num=int(10*(means[1] - means[0])))

    dist1 = w[0] * gamma.pdf(x, alpha[0], scale = 1 / beta[0])
    dist2 = w[1] * gamma.pdf(x, alpha[1], scale = 1 / beta[1])

    return x[np.argmin(np.abs(dist1 - dist2))]
