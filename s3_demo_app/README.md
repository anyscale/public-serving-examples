# S3 Demo App

A Ray Serve app that downloads an image from S3 and returns its size.

## Setup

### 1. Create S3 Bucket & Upload Image

```bash
aws s3api create-bucket \
  --bucket abrar-test-bucket-123 \
  --region us-west-1 \
  --create-bucket-configuration LocationConstraint=us-west-1

aws s3 cp img.jpg s3://abrar-test-bucket-123/img.jpg
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install ray[serve] fastapi aioboto3 locust
```

### 4. Configure AWS Credentials

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-west-1"
```

## Run

### Basic App

```bash
serve run app:app
```

### Optimized App

```bash
serve run app_optimized:app
```

### Load Test with Locust

```bash
locust --host=http://localhost:8000
```

Open http://localhost:8089 to start the test.

## API

```
GET /image-size?s3_uri=s3://abrar-test-bucket-123/img.jpg
```

## Optimizations

| Aspect | Unoptimized | Optimized |
|--------|-------------|-----------|
| Session | New `aioboto3.Session()` per request | Single session reused across requests |
| S3 Client | New client created per request | Persistent client reused across requests |

**Why it matters:**
- **Session reuse**: Avoids re-initializing AWS configuration on every request
- **Persistent client**: Eliminates TCP connection setup, SSL handshake, and auth overhead per request

## Benchmark Results

| Metric | Unoptimized | Optimized | Improvement |
|--------|-------------|-----------|-------------|
| Requests | 224 | 3575 | 16x |
| Median | 830 ms | 53 ms | **15x faster** |
| 95%ile | 1100 ms | 64 ms | 17x faster |
| 99%ile | 1200 ms | 190 ms | 6x faster |
| Average | 830.52 ms | 55.52 ms | **15x faster** |
| Min | 478 ms | 40 ms | 12x faster |
| Max | 1237 ms | 261 ms | 5x faster |
| RPS | 6.2 | 89.6 | **14x higher** |
