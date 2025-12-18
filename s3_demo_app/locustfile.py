from locust import HttpUser, task, constant
import os

# Configure the S3 URI to test with
S3_URI = os.environ.get("S3_URI", "s3://abrar-test-bucket-123/img.jpg")


class S3DemoAppUser(HttpUser):
    """Load test user for the S3 Demo App."""
    
    # Wait between 1 and 3 seconds between tasks
    wait_time = constant(0)
    
    @task
    def get_image_size(self):
        """Test the /image-size endpoint."""
        self.client.get(
            "/image-size",
            params={"s3_uri": S3_URI},
            name="/image-size"
        )
