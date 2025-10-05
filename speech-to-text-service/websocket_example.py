import io
import numpy as np
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import soundfile as sf

from ray import serve


app = FastAPI()


@serve.deployment(
    ray_actor_options={"num_gpus": 1},  # Adjust based on your hardware
    num_replicas=1
)
@serve.ingress(app)
class SpeechToTextDeployment:
    def __init__(self):
        """Initialize Whisper-small model for speech-to-text transcription."""
        print("Loading Whisper-small model...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load Whisper-small model and processor
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-small")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded successfully on {self.device}")
        
        # Whisper expects 16kHz audio
        self.sample_rate = 16000
        self.chunk_duration_ms = 3000  # Process 3 seconds at a time
        
    def preprocess_audio(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array and resample if needed."""
        try:
            # Read audio from bytes
            audio_buffer = io.BytesIO(audio_bytes)
            audio, sr = sf.read(audio_buffer)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Resample if needed
            if sr != self.sample_rate:
                # Simple resampling using librosa-style approach
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            
            return audio
        except Exception as e:
            print(f"Error preprocessing audio: {e}")
            return None
    
    def transcribe(self, audio_array: np.ndarray) -> str:
        """Transcribe audio array to text using Whisper."""
        try:
            # Prepare input features
            input_features = self.processor(
                audio_array,
                sampling_rate=self.sample_rate,
                return_tensors="pt"
            ).input_features.to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.model.generate(input_features)
            
            # Decode the transcription
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True
            )[0]
            
            return transcription.strip()
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""

    @app.websocket("/transcribe")
    async def transcribe_stream(self, ws: WebSocket):
        """WebSocket endpoint for streaming audio transcription."""
        await ws.accept()
        print("Client connected")
        
        try:
            while True:
                # Receive audio data as bytes
                audio_bytes = await ws.receive_bytes()
                
                if len(audio_bytes) == 0:
                    continue
                
                # Preprocess audio
                audio_array = self.preprocess_audio(audio_bytes)
                
                if audio_array is None or len(audio_array) == 0:
                    await ws.send_json({
                        "error": "Failed to process audio",
                        "text": ""
                    })
                    continue
                
                # Transcribe audio
                transcription = self.transcribe(audio_array)
                
                # Send transcription back to client
                await ws.send_json({
                    "text": transcription,
                    "status": "success"
                })
                
                print(f"Transcribed: {transcription}")
                
        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
            try:
                await ws.send_json({
                    "error": str(e),
                    "text": ""
                })
            except:
                pass

    @app.get("/health")
    async def health_check(self):
        """Health check endpoint."""
        return {"status": "healthy", "model": "whisper-small"}


app = SpeechToTextDeployment.bind()
