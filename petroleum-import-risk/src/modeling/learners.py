"""Learned quantile models: LightGBM (global or local) and two small global neural networks.

Every learner has the same interface: fit(train, cols) then predict(test) -> array (n, 5) of
quantiles in target units, sorted so they never cross. One model covers all four tasks; the task
enters through the `h` and `is_sum3` features.
"""
import numpy as np
import pandas as pd

LEVELS = [0.025, 0.1, 0.5, 0.9, 0.975]


class LightGBMQuantile:
    def __init__(self, params, seed=0, with_id=True):
        self.params, self.seed, self.with_id = params, seed, with_id

    def _x(self, frame):
        x = frame[self.cols].astype(float)
        if self.with_id:
            x = x.assign(iso3=pd.Categorical(frame.iso3, categories=self.categories))
        return x

    def fit(self, train, cols):
        import lightgbm as lgb
        self.cols = cols
        self.categories = sorted(train.iso3.unique())
        x, y = self._x(train), train.target.to_numpy()
        self.models = [lgb.LGBMRegressor(objective="quantile", alpha=a, random_state=self.seed, n_jobs=1, **self.params).fit(x, y)
                       for a in LEVELS]
        return self

    def predict(self, test):
        x = self._x(test)
        return np.sort(np.column_stack([m.predict(x) for m in self.models]), axis=1)


def pinball_torch(pred, y, levels):
    import torch
    diff = y.unsqueeze(1) - pred
    return torch.maximum(levels * diff, (levels - 1) * diff).mean()


class NeuralQuantile:
    """kind='mlp': residual MLP on the feature vector (N-BEATS-style block stack).
    kind='gru': GRU over the own-history lags (value + visibility mask), joined with the other features.
    Both use a country embedding. Seeds are trained separately and their quantiles averaged."""

    def __init__(self, params, kind="mlp", seeds=(0, 1, 2, 3, 4), n_lags=18):
        self.params, self.kind, self.seeds, self.n_lags = params, kind, list(seeds), n_lags

    def _arrays(self, frame):
        import torch
        x = frame[self.cols].astype(float).to_numpy()
        mask = ~np.isnan(x)
        x = np.where(mask, (x - self.mu) / self.sd, 0.0)
        x = np.concatenate([x, mask[:, self.mask_cols].astype(float)], axis=1)
        ids = frame.iso3.map(self.index).fillna(len(self.index)).astype(int).to_numpy()
        return torch.tensor(x, dtype=torch.float32), torch.tensor(ids)

    def _net(self, n_in):
        import torch
        from torch import nn
        p = self.params
        hid, emb, drop = p["hidden"], p["embedding"], p["dropout"]
        lag_idx = [self.cols.index(f"lag{j}") for j in range(self.n_lags)]
        lag_mask_idx = [len(self.cols) + self.mask_cols.index(self.cols.index(f"lag{j}")) for j in range(self.n_lags)]
        kind = self.kind

        class Block(nn.Module):
            def __init__(self):
                super().__init__()
                self.f = nn.Sequential(nn.Linear(hid, hid), nn.ReLU(), nn.Dropout(drop), nn.Linear(hid, hid))

            def forward(self, z):
                return torch.relu(z + self.f(z))

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(len(self_index) + 1, emb)
                if kind == "gru":
                    self.gru = nn.GRU(2, hid // 2, batch_first=True)
                    n_static = n_in + emb + hid // 2
                else:
                    n_static = n_in + emb
                self.inp = nn.Linear(n_static, hid)
                self.blocks = nn.Sequential(Block(), Block(), Block())
                self.out = nn.Linear(hid, len(LEVELS))

            def forward(self, x, ids):
                parts = [x, self.emb(ids)]
                if kind == "gru":
                    seq = torch.stack([x[:, lag_idx], x[:, lag_mask_idx]], dim=2).flip(1)  # oldest month first
                    _, h = self.gru(seq)
                    parts.append(h[-1])
                z = torch.relu(self.inp(torch.cat(parts, dim=1)))
                return self.out(self.blocks(z))

        self_index = self.index
        return Net()

    def fit(self, train, cols):
        import torch
        self.cols = list(cols)
        x = train[self.cols].astype(float)
        self.mu, self.sd = x.mean().to_numpy(), x.std().replace(0, 1).fillna(1).to_numpy()
        self.mu = np.nan_to_num(self.mu)
        self.mask_cols = [i for i, c in enumerate(self.cols) if c.startswith(("lag", "seas")) or c in ("uv_asof", "fx_chg12", "cpi_chg12")]
        self.index = {k: i for i, k in enumerate(sorted(train.iso3.unique()))}
        X, ids = self._arrays(train)
        y = torch.tensor(train.target.to_numpy(), dtype=torch.float32)
        levels = torch.tensor(LEVELS, dtype=torch.float32)
        p = self.params
        self.nets = []
        torch.set_num_threads(1)
        for seed in self.seeds:
            torch.manual_seed(seed)
            gen = torch.Generator().manual_seed(seed)
            net = self._net(X.shape[1])
            opt = torch.optim.AdamW(net.parameters(), lr=p["learning_rate"], weight_decay=p["weight_decay"])
            n = len(y)
            for _ in range(p["epochs"]):
                net.train()
                perm = torch.randperm(n, generator=gen)
                for i in range(0, n, p["batch_size"]):
                    b = perm[i:i + p["batch_size"]]
                    opt.zero_grad()
                    loss = pinball_torch(net(X[b], ids[b]), y[b], levels)
                    loss.backward()
                    opt.step()
            net.eval()
            self.nets.append(net)
        return self

    def predict(self, test):
        import torch
        X, ids = self._arrays(test)
        with torch.no_grad():
            preds = np.mean([net(X, ids).numpy() for net in self.nets], axis=0)
        return np.sort(preds, axis=1)
