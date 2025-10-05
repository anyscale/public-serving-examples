import asyncio
import json
import wave
import io
import pyaudio
import websockets
import argparse
from typing import Optional


class ConversationClient:
    """Client that maintains a persistent WebSocket connection for conversation."""
    
    def __init__(self, server_url="ws://localhost:8000/", bearer_token=None):
        self.server_url = server_url + "transcribe"
        self.bearer_token = bearer_token
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        
        # Audio configuration
        self.chunk_duration = 3  # seconds per audio chunk
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16
        self.chunk_size = 1024
        
        self.audio = pyaudio.PyAudio()
        self.conversation_history = []
        
    async def connect(self):
        """Establish WebSocket connection."""
        extra_headers = {}
        if self.bearer_token:
            extra_headers["Authorization"] = f"Bearer {self.bearer_token}"
        
        print(f"🔗 Connecting to: {self.server_url}")
        if self.bearer_token:
            print(f"🔑 Using bearer token: {self.bearer_token[:20]}...")
        
        self.websocket = await websockets.connect(
            self.server_url,
            extra_headers=extra_headers if extra_headers else None
        )
        print(f"✓ Connected to {self.server_url}")
        print("=" * 70)
        print("Conversation Mode - Single persistent connection")
        print("=" * 70)
        print()
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            print("\n✓ Disconnected from server")
    
    def record_audio_chunk(self, duration: int) -> bytes:
        """Record audio for specified duration and return as WAV bytes."""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        print(f"🎤 Recording for {duration} seconds...", end=" ", flush=True)
        frames = []
        
        for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
            data = stream.read(self.chunk_size)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        print("✓")
        
        # Convert to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        return wav_buffer.getvalue()
    
    async def send_audio_chunk(self, audio_data: bytes, turn_number: int):
        """Send a single audio chunk over the existing connection."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        print(f"📤 Sending audio chunk #{turn_number}...", end=" ", flush=True)
        await self.websocket.send(audio_data)
        print("✓")
    
    async def receive_transcription(self, turn_number: int) -> str:
        """Receive transcription from the server."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        print(f"📥 Waiting for transcription #{turn_number}...", end=" ", flush=True)
        response = await self.websocket.recv()
        result = json.loads(response)
        print("✓")
        
        if result.get("status") == "success":
            return result.get("text", "")
        else:
            error = result.get("error", "Unknown error")
            print(f"\n✗ Error: {error}")
            return ""
    
    async def conversation_turn(self, turn_number: int):
        """Handle one turn of the conversation."""
        print(f"\n{'─' * 70}")
        print(f"Turn #{turn_number}")
        print(f"{'─' * 70}")
        
        # Record audio
        audio_data = self.record_audio_chunk(self.chunk_duration)
        
        # Send over the SAME connection
        await self.send_audio_chunk(audio_data, turn_number)
        
        # Receive transcription over the SAME connection
        transcription = await self.receive_transcription(turn_number)
        
        if transcription:
            print(f"\n💬 You said: \"{transcription}\"")
            self.conversation_history.append({
                "turn": turn_number,
                "text": transcription
            })
        
        return transcription
    
    async def run_conversation(self, num_turns: int = 5):
        """Run a multi-turn conversation over a single connection."""
        try:
            # Connect once
            await self.connect()
            
            print("Starting conversation...")
            print("Speak clearly into your microphone for each turn.")
            print(f"You'll have {num_turns} turns to speak.\n")
            
            # Multiple turns over the SAME connection
            for turn in range(1, num_turns + 1):
                input(f"Press Enter when ready for turn {turn}/{num_turns}...")
                
                transcription = await self.conversation_turn(turn)
                
                if not transcription:
                    print("⚠ No transcription received, but connection remains open")
                
                # Small delay between turns
                await asyncio.sleep(0.5)
            
            # Show conversation summary
            print("\n" + "=" * 70)
            print("Conversation Summary")
            print("=" * 70)
            for item in self.conversation_history:
                print(f"Turn {item['turn']}: {item['text']}")
            print("=" * 70)
            
        finally:
            # Disconnect once at the end
            await self.disconnect()
            self.audio.terminate()


class FileConversationClient:
    """Simulates a conversation using pre-recorded audio files over a single connection."""
    
    def __init__(self, server_url="ws://localhost:8000/", bearer_token=None):
        self.server_url = server_url + "transcribe"
        self.bearer_token = bearer_token
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.conversation_history = []
    
    async def connect(self):
        """Establish WebSocket connection."""
        extra_headers = {}
        if self.bearer_token:
            extra_headers["Authorization"] = f"Bearer {self.bearer_token}"
        
        print(f"🔗 Connecting to: {self.server_url}")
        if self.bearer_token:
            print(f"🔑 Using bearer token: {self.bearer_token[:20]}...")
        
        self.websocket = await websockets.connect(
            self.server_url,
            extra_headers=extra_headers if extra_headers else None
        )
        print(f"✓ Connected to {self.server_url}")
        print("=" * 70)
        print("File-based Conversation - Single persistent connection")
        print("=" * 70)
        print()
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            print("\n✓ Disconnected from server")
    
    async def send_and_receive(self, audio_file: str, turn_number: int):
        """Send audio file and receive transcription."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        print(f"\n{'─' * 70}")
        print(f"Turn #{turn_number}: Processing {audio_file}")
        print(f"{'─' * 70}")
        
        # Read audio file
        try:
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
        except FileNotFoundError:
            print(f"✗ File not found: {audio_file}")
            return None
        
        # Send audio
        print(f"📤 Sending audio...", end=" ", flush=True)
        await self.websocket.send(audio_data)
        print("✓")
        
        # Receive transcription (on the SAME connection)
        print(f"📥 Waiting for transcription...", end=" ", flush=True)
        response = await self.websocket.recv()
        result = json.loads(response)
        print("✓")
        
        if result.get("status") == "success":
            text = result.get("text", "")
            print(f"\n💬 Transcription: \"{text}\"")
            self.conversation_history.append({
                "turn": turn_number,
                "file": audio_file,
                "text": text
            })
            return text
        else:
            error = result.get("error", "Unknown error")
            print(f"\n✗ Error: {error}")
            return None
    
    async def run_conversation(self, audio_files: list):
        """Process multiple audio files as a conversation over a single connection."""
        try:
            # Connect once
            await self.connect()
            
            print(f"Processing {len(audio_files)} audio files as a conversation...\n")
            
            # Process each file over the SAME connection
            for turn, audio_file in enumerate(audio_files, 1):
                await self.send_and_receive(audio_file, turn)
                
                # Small delay between turns
                await asyncio.sleep(0.3)
            
            # Show conversation summary
            print("\n" + "=" * 70)
            print("Conversation Summary")
            print("=" * 70)
            for item in self.conversation_history:
                print(f"Turn {item['turn']} ({item['file']}): {item['text']}")
            print("=" * 70)
            print(f"\nTotal turns: {len(self.conversation_history)}")
            print(f"All processed over a SINGLE WebSocket connection!")
            
        finally:
            # Disconnect once at the end
            await self.disconnect()


async def demo_with_downloaded_samples(server_url="ws://localhost:8000/", bearer_token=None):
    """Demo using samples downloaded from Hugging Face."""
    import requests
    import os
    
    print("=" * 70)
    print("Conversation Demo with Hugging Face Samples")
    print("=" * 70)
    print()
    
    # Download sample files
    samples = [
        {
            "url": "https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/1.flac",
            "name": "conversation_turn_1.flac"
        },
        {
            "url": "https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/2.flac",
            "name": "conversation_turn_2.flac"
        },
        {
            "url": "https://cdn-media.huggingface.co/speech_samples/sample1.flac",
            "name": "conversation_turn_3.flac"
        },
    ]
    
    os.makedirs("conversation_samples", exist_ok=True)
    audio_files = []
    
    print("Downloading sample audio files...")
    for sample in samples:
        filepath = os.path.join("conversation_samples", sample["name"])
        
        if not os.path.exists(filepath):
            print(f"  Downloading {sample['name']}...", end=" ", flush=True)
            response = requests.get(sample["url"], timeout=30)
            with open(filepath, "wb") as f:
                f.write(response.content)
            print("✓")
        else:
            print(f"  Using cached {sample['name']} ✓")
        
        audio_files.append(filepath)
    
    print()
    
    # Run conversation
    client = FileConversationClient(server_url=server_url, bearer_token=bearer_token)
    await client.run_conversation(audio_files)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Whisper Speech-to-Text - Conversation Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="ws://localhost:8000/",
        help="WebSocket URL (default: ws://localhost:8000/)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Bearer token for authentication"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode with Hugging Face samples"
    )
    
    parser.add_argument(
        "audio_files",
        nargs="*",
        help="Audio files to process as conversation turns"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("Whisper Speech-to-Text - Conversation Mode")
    print("Single WebSocket Connection with Multiple Turns")
    print("=" * 70)
    print()
    
    if args.demo:
        # Demo mode
        await demo_with_downloaded_samples(server_url=args.url, bearer_token=args.token)
    elif args.audio_files:
        # File mode with provided audio files
        print(f"Processing {len(args.audio_files)} files as a conversation...\n")
        client = FileConversationClient(server_url=args.url, bearer_token=args.token)
        await client.run_conversation(args.audio_files)
    else:
        # Interactive mode
        # Live microphone conversation
        num_turns = int(input("How many conversation turns? (default 5): ").strip() or "5")
        client = ConversationClient(server_url=args.url, bearer_token=args.token)
        await client.run_conversation(num_turns)

if __name__ == "__main__":
    print()
    print("💡 Key Feature: This maintains a SINGLE WebSocket connection")
    print("   and sends/receives multiple messages over it.")
    print()
    print("Usage:")
    print("  Interactive:      python conversation_example.py --url <ws_url> --token <bearer_token>")
    print("  From files:       python conversation_example.py --url <ws_url> --token <bearer_token> file1.wav file2.wav")
    print("  Demo mode:        python conversation_example.py --demo --url <ws_url> --token <bearer_token>")
    print("  Show help:        python conversation_example.py --help")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Conversation interrupted by user")
    except Exception as e:
        import traceback
        print(f"\n\n✗ Error: {e}")
        print(f"\nError type: {type(e).__name__}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\nMake sure the server is running and accessible.")
