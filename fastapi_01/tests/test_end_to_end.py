import asyncio
import time

import pytest
import ray
import requests
from ray import serve

# Import config
from example_app.config import RAY_ADDRESS

# Import the deployment classes
from example_app.serve.serve_config import INGRESS_APP_NAME

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "admin"
TEST_PASSWORD = "password"


@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token for API tests."""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def api_headers(auth_token):
    """Get headers with authentication token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session", autouse=True)
def ray_setup():
    """Initialize Ray and Ray Serve for testing."""
    if not ray.is_initialized():
        ray.init(address=RAY_ADDRESS, namespace="nlp_pipeline")

    from example_app.main import serve_ingress_app

    serve.run(serve_ingress_app, name=INGRESS_APP_NAME, route_prefix="/")

    time.sleep(3)

    yield

    # Cleanup
    serve.shutdown()


@pytest.fixture(scope="session")
def deployment_handles(ray_setup):
    """Get handles to all deployments."""
    from ray.serve import get_deployment_handle

    return {
        "sentiment_analyzer": get_deployment_handle(
            "sentiment_analyzer", app_name=INGRESS_APP_NAME
        ),
        "text_classifier": get_deployment_handle(
            "text_classifier", app_name=INGRESS_APP_NAME
        ),
        "entity_recognizer": get_deployment_handle(
            "entity_recognizer", app_name=INGRESS_APP_NAME
        ),
        "streaming_analyzer": get_deployment_handle(
            "streaming_analyzer", app_name=INGRESS_APP_NAME
        ).options(stream=True),
    }


class TestAPIEndpoints:
    """Test suite for REST API endpoints."""

    def test_health_check(self, api_headers):
        """Test the health check endpoint."""
        response = requests.get(f"{BASE_URL}/health", headers=api_headers)
        assert response.status_code == 200
        health_data = response.json()
        assert "models" in health_data
        assert all(isinstance(v, bool) for v in health_data["models"].values())

    def test_user_info(self, api_headers):
        """Test getting user information."""
        response = requests.get(f"{BASE_URL}/users/me", headers=api_headers)
        assert response.status_code == 200
        user_data = response.json()
        assert "username" in user_data
        assert user_data["username"] == TEST_USERNAME

    def test_sentiment_analysis(self, api_headers):
        """Test sentiment analysis endpoint."""
        test_text = "I really enjoyed this movie, it was fantastic!"
        response = requests.post(
            f"{BASE_URL}/sentiment", headers=api_headers, json={"text": test_text}
        )
        assert response.status_code == 200
        result = response.json()
        assert "sentiment" in result
        assert "score" in result
        assert 0 <= result["score"] <= 1

    def test_entity_recognition(self, api_headers):
        """Test entity recognition endpoint."""
        test_text = (
            "Apple CEO Tim Cook announced the new iPhone in Cupertino, California."
        )
        response = requests.post(
            f"{BASE_URL}/entities", headers=api_headers, json={"text": test_text}
        )
        assert response.status_code == 200
        result = response.json()
        assert "entities" in result
        assert len(result["entities"]) > 0
        assert all("text" in entity for entity in result["entities"])

    def test_text_classification(self, api_headers):
        """Test text classification endpoint."""
        test_text = "The iPhone 13 Pro Max has an amazing camera system."
        test_labels = ["technology", "sports", "politics", "entertainment"]
        response = requests.post(
            f"{BASE_URL}/classify",
            headers=api_headers,
            json={"text": test_text, "labels": test_labels},
        )
        assert response.status_code == 200
        result = response.json()
        assert "labels" in result
        assert len(result["labels"]) == len(test_labels)
        assert all("score" in label for label in result["labels"])


class TestRayServeDeployments:
    """Test suite for Ray Serve deployments."""

    @pytest.mark.asyncio
    async def test_sentiment_analyzer(self, deployment_handles):
        """Test sentiment analyzer deployment."""
        test_text = "This product exceeded my expectations in every way possible!"
        result = await deployment_handles["sentiment_analyzer"].analyze.remote(
            test_text
        )

        assert "sentiment" in result
        assert "score" in result
        assert "processing_time" in result
        assert 0 <= result["score"] <= 1

    @pytest.mark.asyncio
    async def test_text_classifier(self, deployment_handles):
        """Test text classifier deployment."""
        test_text = "The president announced new economic policies yesterday."
        test_labels = ["politics", "economics", "sports", "technology"]

        result = await deployment_handles["text_classifier"].classify.remote(
            test_text, test_labels
        )

        assert "labels" in result
        assert len(result["labels"]) == len(test_labels)
        assert all("score" in label for label in result["labels"])
        assert "processing_time" in result

    @pytest.mark.asyncio
    async def test_entity_recognizer(self, deployment_handles):
        """Test entity recognizer deployment."""
        test_text = (
            "Google and Microsoft are competing in the cloud services market in Europe."
        )
        result = await deployment_handles[
            "entity_recognizer"
        ].recognize_entities.remote(test_text)

        assert "entities" in result
        assert len(result["entities"]) > 0
        assert all("text" in entity for entity in result["entities"])
        assert "processing_time" in result

    @pytest.mark.asyncio
    async def test_streaming_analyzer(self, deployment_handles):
        """Test streaming analyzer deployment."""
        test_text = """The Apple conference in San Francisco was attended by Tim Cook, who announced new products. 
        Microsoft and Google were also represented at the event."""

        chunks = []
        async for chunk_result in deployment_handles[
            "streaming_analyzer"
        ].stream_analysis.remote(test_text):
            chunks.append(chunk_result)
            assert "chunk_id" in chunk_result
            assert "chunk_text" in chunk_result
            assert "progress" in chunk_result
            assert 0 <= chunk_result["progress"] <= 1

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_document_analysis(self, deployment_handles):
        """Test document analysis endpoint."""
        test_text = """The Apple conference in San Francisco was attended by Tim Cook, who announced new products. 
        Microsoft and Google were also represented at the event."""

        result = (
            await deployment_handles["streaming_analyzer"]
            .options(stream=False)
            .analyze_document.remote(test_text)
        )

        assert "text_length" in result
        assert "chunk_count" in result
        assert result["text_length"] > 0
        assert result["chunk_count"] > 0

        if "sentiment" in result:
            assert "overall" in result["sentiment"]
            assert "average_score" in result["sentiment"]
            assert "sentiment_by_chunk" in result["sentiment"]

        if "entities" in result:
            assert "count" in result["entities"]
            assert "by_type" in result["entities"]
            assert "all_entities" in result["entities"]


class TestPerformance:
    """Test suite for performance benchmarking."""

    @pytest.mark.asyncio
    async def test_throughput(self, deployment_handles):
        """Test throughput of all models with concurrent requests."""
        num_requests = 10

        # Test data
        sentiment_text = "This product exceeded my expectations in every way possible!"
        classification_text = "The president announced new economic policies yesterday."
        classification_labels = ["politics", "economics", "sports", "technology"]
        entity_text = (
            "Google and Microsoft are competing in the cloud services market in Europe."
        )

        # Test sentiment analyzer throughput
        start_time = time.time()
        tasks = [
            deployment_handles["sentiment_analyzer"].analyze.remote(sentiment_text)
            for _ in range(num_requests)
        ]
        results = await asyncio.gather(*tasks)
        sentiment_time = time.time() - start_time

        # Test text classifier throughput
        start_time = time.time()
        tasks = [
            deployment_handles["text_classifier"].classify.remote(
                classification_text, classification_labels
            )
            for _ in range(num_requests)
        ]
        results = await asyncio.gather(*tasks)
        classifier_time = time.time() - start_time

        # Test entity recognizer throughput
        start_time = time.time()
        tasks = [
            deployment_handles["entity_recognizer"].recognize_entities.remote(
                entity_text
            )
            for _ in range(num_requests)
        ]
        results = await asyncio.gather(*tasks)
        entity_time = time.time() - start_time

        # Assert reasonable performance
        assert sentiment_time < 100  # Should process 10 requests in under 10 seconds
        assert classifier_time < 100
        assert entity_time < 100

        # Calculate and verify throughput
        sentiment_throughput = num_requests / sentiment_time
        classifier_throughput = num_requests / classifier_time
        entity_throughput = num_requests / entity_time

        assert sentiment_throughput > 0  # At least 1 request per second
        assert classifier_throughput > 0
        assert entity_throughput > 0
