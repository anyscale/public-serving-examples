from fastapi import FastAPI
import ray
from ray import serve
from typing import Callable, Dict, Any

from example_app.serve.deployments.sentiment import SentimentAnalyzer
from example_app.serve.deployments.classification import TextClassifier
from example_app.serve.deployments.entities import EntityRecognizer
from example_app.serve.deployments.streaming_analyzer import StreamingAnalyzer
from ray.serve.api import DeploymentHandle, Application
from example_app.config import RAY_ADDRESS
from example_app.serve.ingress_deployment import IngressDeployment


INGRESS_APP_NAME = "ingress-app"


def get_serve_app(fastapi_app: FastAPI, app_init_func: Callable = None) -> Application:
    # Deploy the ingress deployment
    serve_ingress_app: Application = (
        # TODO: This ingress api doesn't feel right. Allow passing ingress deployment into the function.
        serve.deployment(serve.ingress(fastapi_app, app_init_func)(IngressDeployment))
        .options(
            name="ingress-deployment",
            num_replicas=1,
        )
        .bind(
            SentimentAnalyzer.bind(),
            TextClassifier.bind(),
            EntityRecognizer.bind(),
            StreamingAnalyzer.bind(),
        )
    )

    return serve_ingress_app


def get_deployment(name: str) -> DeploymentHandle:
    """Get deployment handle by name."""
    return serve.get_deployment_handle(name, app_name=INGRESS_APP_NAME)
