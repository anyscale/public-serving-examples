from ray import serve
from fastapi import FastAPI
import aioboto3
from urllib.parse import urlparse
import logging

logger = logging.getLogger("ray.serve")

app = FastAPI()


@serve.deployment(name="s3_demo_app_optimized")
@serve.ingress(app)
class S3DemoAppOptimized:
    def __init__(self):
        # Reuse session across requests instead of creating new one each time
        self._session = aioboto3.Session()
        # Keep a persistent client reference
        self._s3_client = None

    async def _get_client(self):
        """Get or create a reusable S3 client."""
        if self._s3_client is None:
            self._s3_client = await self._session.client("s3").__aenter__()
        return self._s3_client

    async def _fetch_from_s3_async(self, s3_uri: str) -> bytes:
        try:
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            
            if not bucket or not key:
                raise ValueError(f"Invalid S3 URI format: {s3_uri}. Expected s3://bucket/key")
            
            logger.info(f"Fetching image from S3 asynchronously: bucket={bucket}, key={key}")
            
            # Use persistent client instead of creating new session each time
            s3_client = await self._get_client()
            response = await s3_client.get_object(Bucket=bucket, Key=key)
            body = response["Body"]
            
            try:
                async with body as stream:
                    image_bytes = await stream.read()
            except TypeError:
                image_bytes = await body.read()
            
            logger.info(f"Successfully fetched {len(image_bytes)} bytes from S3 asynchronously")
            return image_bytes
        except Exception as e:
            logger.error(f"Failed to fetch image from S3 URI {s3_uri} asynchronously: {e}")
            raise ValueError(f"Failed to fetch image from S3: {str(e)}")

    @app.get("/image-size")
    async def get_image_size(self, s3_uri: str):
        image_bytes = await self._fetch_from_s3_async(s3_uri)
        return {
            "s3_uri": s3_uri,
            "size_bytes": len(image_bytes),
            "size_kb": round(len(image_bytes) / 1024, 2),
            "size_mb": round(len(image_bytes) / (1024 * 1024), 2)
        }


app = S3DemoAppOptimized.bind()
