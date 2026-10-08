import numpy as np
from scipy.special import logsumexp
import recovery_pitch as source


def responsibilities(x, model):
    z = (x[:, source.RECIPE['columns']] - np.array(model['mean'])) / np.array(model['scale'])
    variance = np.array(model['variance'])
    centers = np.array(model['centers'])
    logs = np.log(model['weights']) - .5 * (
        np.log(2 * np.pi * variance).sum(axis=1)[None, :]
        + ((z[:, None, :] - centers[None, :, :]) ** 2 / variance[None, :, :]).sum(axis=2))
    return np.exp(logs - logsumexp(logs, axis=1, keepdims=True))


def fit_mapping(model, bank):
    names = model['fit_files']
    n = min(len(bank[name]['x']) for name in names)
    features, targets, indices = [], [], {}
    for name in names:
        ix = np.round(np.linspace(0, len(bank[name]['x']) - 1, n)).astype(int)
        indices[name] = ix.tolist()
        features.append(bank[name]['x'][ix])
        labels = bank[name]['labels'][ix]
        assert np.isin(labels, ['v', 'uv', 'sil']).all()
        targets.append(labels == 'v')
    resp = responsibilities(np.vstack(features), model)
    mass = resp.sum(axis=0)
    voiced = resp.T @ np.concatenate(targets).astype(float)
    weights = (voiced + 1.) / (mass + 2.)
    return dict(fit_files=list(names), seed=model['seed'], indices=indices,
                mass=mass.tolist(), voiced_mass=voiced.tolist(), weights=weights.tolist())


def mapped_score(x, model, mapping):
    return responsibilities(x, model) @ np.array(mapping['weights'])
