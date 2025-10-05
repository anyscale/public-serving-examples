# Speech-to-Text Service

WebSocket-based real-time speech transcription service deployed on Anyscale.

## Quick Start

1. **Build Docker image**

2. **Update service config**
   - Set `image_uri` in `service.yaml` to your built image

3. **Deploy service**
   ```bash
   anyscale service deploy -f service.yaml
   ```

4. **Run client**
   ```bash
   python conversation_example.py \
     --url "wss://<service-url>" \
     --token "<bearer-token>" \
     --demo
   ```
   
   Get the URL and token from the Anyscale Services UI.
   