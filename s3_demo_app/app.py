from ray import serve
from fastapi import FastAPI
import aioboto3
from urllib.parse import urlparse
import logging

logger = logging.getLogger("ray.serve")

app = FastAPI()

@serve.deployment(name="s3_demo_app")
@serve.ingress(app)
class S3DemoApp:
    def __init__(self):
        pass

    async def _fetch_from_s3_async(self, s3_uri: str) -> bytes:
        try:
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            
            if not bucket or not key:
                raise ValueError(f"Invalid S3 URI format: {s3_uri}. Expected s3://bucket/key")
            
            logger.info(f"Fetching image from S3 asynchronously: bucket={bucket}, key={key}")
            session = aioboto3.Session()
            async with session.client("s3") as s3_client:
                response = await s3_client.get_object(Bucket=bucket, Key=key)
                body = response["Body"]
                # aioboto3 streaming body supports async read
                try:
                    async with body as stream:
                        image_bytes = await stream.read()
                except TypeError:
                    # Fallback for older versions where Body isn't an async context manager
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

app = S3DemoApp.bind()
