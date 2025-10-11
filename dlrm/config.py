from dataclasses import dataclass
from typing import List


@dataclass
class DLRMArgs:
    num_dense_features: int
    num_sparse_features: int
    emb_dim: int
    cardinality: int
    bottom_mlp: List[int]
    top_mlp: List[int]
    use_gpu: bool

config = DLRMArgs(
    num_dense_features=13,
    num_sparse_features=26,
    emb_dim=64,
    cardinality=100000,
    bottom_mlp=[256, 64],
    top_mlp=[256, 128, 64],
    use_gpu=False,
)
