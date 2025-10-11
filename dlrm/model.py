from typing import List

import torch
import torch.nn as nn
from fastapi import FastAPI

# -----------------------------
# Minimal DLRM-style model
# -----------------------------
class DotInteraction(nn.Module):
    def __init__(self,):
        super().__init__()

    def forward(self, dense: torch.Tensor, embs: List[torch.Tensor]) -> torch.Tensor:
        # dense: [B, D]  ; embs: list of [B, D]
        # concatenate dense to the list for pairwise dots
        all_feats = [dense] + embs
        # Stack to [B, N, D]
        T = torch.stack(all_feats, dim=1)
        # Pairwise dot-products: [B, N, N]
        Z = torch.bmm(T, T.transpose(1, 2))
        # Take upper triangle (excluding diagonal) and flatten: [B, N*(N-1)/2]
        B, N, _ = Z.shape
        iu = torch.triu_indices(N, N, offset=1, device=Z.device)
        Z_triu = Z[:, iu[0], iu[1]]
        return Z_triu


class MiniDLRM(nn.Module):
    def __init__(
        self,
        num_dense_features: int,
        num_sparse_features: int,
        emb_dim: int,
        cardinalities: List[int],
        bottom_mlp: List[int],
        top_mlp: List[int],
        device: str = "cpu",
    ):
        super().__init__()
        assert len(cardinalities) == num_sparse_features

        self.device = device
        self.emb_tables = nn.ModuleList(
            [
                nn.Embedding(card, emb_dim, device=device)
                for card in cardinalities
            ]
        )
        # bottom MLP for dense
        layers = []
        in_dim = num_dense_features
        for h in bottom_mlp:
            layers += [nn.Linear(in_dim, h, device=device), nn.ReLU()]
            in_dim = h
        self.bottom_mlp = nn.Sequential(*layers)

        self.interact = DotInteraction()

        # top MLP after concat([bottom], [pairwise_dots])
        # input dim = bottom_out + C(n_feats,2) where n_feats = 1 + num_sparse_features
        bottom_out = bottom_mlp[-1] if bottom_mlp else num_dense_features
        n_feats = 1 + num_sparse_features
        pairwise = n_feats * (n_feats - 1) // 2
        top_in = bottom_out + pairwise

        layers = []
        in_dim = top_in
        for h in top_mlp:
            layers += [nn.Linear(in_dim, h, device=device), nn.ReLU()]
            in_dim = h
        layers += [nn.Linear(in_dim, 1, device=device)]
        self.top_mlp = nn.Sequential(*layers)

    @torch.inference_mode()
    def forward(self, dense: torch.Tensor, sparse: torch.Tensor) -> torch.Tensor:
        # dense: [B, Fd]; sparse: [B, Fs] integer IDs per feature (one-hot via embedding)
        embs = []
        # sparse is [B, Fs]; take each column and look up
        for i, emb in enumerate(self.emb_tables):
            embs.append(emb(sparse[:, i]))
        # bottom MLP
        z0 = self.bottom_mlp(dense)
        # interaction
        zi = self.interact(z0, embs)
        # top MLP on concat
        x = torch.cat([z0, zi], dim=1)
        out = self.top_mlp(x)
        return torch.sigmoid(out).squeeze(-1)  # [B]

# -----------------------------
# Ray Serve deployment
# -----------------------------
app = FastAPI()

def build_model_from_args(args):
    device = "cuda" if torch.cuda.is_available() and args.use_gpu else "cpu"
    # Cardinalities: each categorical feature has vocabulary size 'args.cardinality'
    cards = [args.cardinality] * args.num_sparse_features
    model = MiniDLRM(
        num_dense_features=args.num_dense_features,
        num_sparse_features=args.num_sparse_features,
        emb_dim=args.emb_dim,
        cardinalities=cards,
        bottom_mlp=args.bottom_mlp,
        top_mlp=args.top_mlp,
        device=device,
    )
    model.eval()
    return model, device
