import numpy as np
from scipy.special import logsumexp

EPSILON = 1e-6


def fit_transitions(model, bank):
    initial = np.ones(2)
    counts = np.ones((2, 2))
    for name in model['fit_files']:
        labels = bank[name]['labels']
        assert len(labels) and np.isin(labels, ['v', 'uv', 'sil']).all()
        state = (labels == 'v').astype(int)
        initial[state[0]] += 1
        np.add.at(counts, (state[:-1], state[1:]), 1)
    return dict(fit_files=list(model['fit_files']), seed=model['seed'],
                initial_counts=initial.tolist(), transition_counts=counts.tolist(),
                initial=(initial/initial.sum()).tolist(),
                transition=(counts/counts.sum(axis=1, keepdims=True)).tolist())


def smooth_probability(probability, fitted):
    probability = np.asarray(probability, float)
    assert probability.ndim == 1 and len(probability) and np.isfinite(probability).all()
    assert ((probability >= 0) & (probability <= 1)).all()
    p = np.clip(probability, EPSILON, 1-EPSILON)
    unary = np.log(np.column_stack((1-p, p)))
    transition = np.log(np.array(fitted['transition']))
    alpha = np.empty_like(unary)
    beta = np.zeros_like(unary)
    alpha[0] = np.log(fitted['initial']) + unary[0]
    for t in range(1, len(p)):
        alpha[t] = unary[t] + logsumexp(alpha[t-1][:, None]+transition, axis=0)
    for t in range(len(p)-2, -1, -1):
        beta[t] = logsumexp(transition+unary[t+1][None, :]+beta[t+1][None, :], axis=1)
    log_mass = alpha + beta
    result = np.exp(log_mass-logsumexp(log_mass, axis=1, keepdims=True))[:, 1]
    assert np.isfinite(result).all()
    return result
