from fastapi import FastAPI
import torch
from ray import serve
import numpy as np
from model import build_model_from_args
from config import config


app = FastAPI()

@serve.deployment(
    name="ranker_deployment",
    max_ongoing_requests=1000,
)
class RankerDeployment:
    def __init__(self):
        self.model, self.device = build_model_from_args(config)
        # Pre-allocate a dummy tensor to force weights onto device
        _ = self.model(
            torch.zeros((1, config.num_dense_features), device=self.device),
            torch.zeros((1, config.num_sparse_features), dtype=torch.long, device=self.device),
        )

    @serve.batch(max_batch_size=64, batch_wait_timeout_s=0.01)
    async def rank(self, payloads: list):
        # payloads is a list of dicts, each containing "dense" and "sparse"
        # Flatten all samples from all payloads into a single batch
        all_dense = []
        all_sparse = []
        batch_sizes = []
        
        for payload in payloads:
            dense_samples = payload["dense"]
            sparse_samples = payload["sparse"]
            batch_sizes.append(len(dense_samples))
            all_dense.extend(dense_samples)
            all_sparse.extend(sparse_samples)
        
        # Convert to tensors
        dense = torch.tensor(all_dense, dtype=torch.float32, device=self.device)
        sparse = torch.tensor(all_sparse, dtype=torch.long, device=self.device)
        
        with torch.inference_mode():
            y = self.model(dense, sparse)
        
        # Split results back into separate responses for each request
        scores = y.detach().cpu().tolist()
        results = []
        start_idx = 0
        for batch_size in batch_sizes:
            end_idx = start_idx + batch_size
            results.append({"scores": scores[start_idx:end_idx]})
            start_idx = end_idx
        
        return results


@serve.deployment(
    name="candidate_generator",
    max_ongoing_requests=1000,
)
class CandidateGenerator:
    def __init__(self, ranker_deployment):
        self.ranker_deployment = ranker_deployment
    
    def synth_batch(self, config):
        B = 64
        dense = np.random.random((B, config.num_dense_features)).astype("float32")
        sparse = np.random.randint(
            low=0, high=config.cardinality,
            size=(B, config.num_sparse_features),
            dtype="int64",
        )
        return {"dense": dense.tolist(), "sparse": sparse.tolist()}
    
    async def generate(self, user_id: int):
        return await self.ranker_deployment.rank.remote(self.synth_batch(config))


@serve.deployment(
    name="ingress_deployment",
    max_ongoing_requests=1000,
)
@serve.ingress(app)
class IngressDeployment:
    def __init__(self, candidate_generator):
        self.candidate_generator = candidate_generator
    
    @app.get("/")
    async def infer(self, user_id: int):
        return await self.candidate_generator.generate.remote(user_id)

recsys_app = IngressDeployment.bind(
    CandidateGenerator.bind(
        RankerDeployment.bind()
    )
)
