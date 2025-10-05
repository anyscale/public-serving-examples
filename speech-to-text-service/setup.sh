#!/bin/bash

echo "========================================================================="
echo "Whisper Speech-to-Text Service - Complete Setup"
echo "========================================================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
else
    OS=$(uname -s)
fi

echo "✓ Detected OS: $OS"
echo ""

# Install system dependencies
echo "========================================================================="
echo "Step 1: Installing System Dependencies"
echo "========================================================================="
echo ""

if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    echo "Installing packages for Ubuntu/Debian..."
    echo "  - gcc, python3-dev (for compiling PyAudio)"
    echo "  - portaudio19-dev (audio I/O library)"
    echo "  - ffmpeg (audio/video processing)"
    echo ""
    
    sudo apt-get update
    sudo apt-get install -y gcc python3-dev portaudio19-dev ffmpeg
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ System dependencies installed successfully!"
    else
        echo ""
        echo "✗ Error installing system dependencies. Please check errors above."
        exit 1
    fi
    
elif [[ "$OS" == "Darwin" ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing packages for macOS..."
    echo "  - portaudio (audio I/O library)"
    echo "  - ffmpeg (audio/video processing)"
    echo ""
    
    if command -v brew &> /dev/null; then
        brew install portaudio ffmpeg
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✓ System dependencies installed successfully!"
        else
            echo ""
            echo "✗ Error installing system dependencies. Please check errors above."
            exit 1
        fi
    else
        echo "✗ Homebrew not found. Please install it first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
else
    echo "⚠ Unsupported OS: $OS"
    echo "Please manually install: gcc, portaudio, ffmpeg"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "========================================================================="
echo "Step 2: Installing Python Dependencies"
echo "========================================================================="
echo ""
echo "This may take a few minutes (downloading ~2GB for PyTorch)..."
echo ""

pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Python dependencies installed successfully!"
else
    echo ""
    echo "✗ Error installing Python dependencies. Please check errors above."
    exit 1
fi

echo ""
echo "========================================================================="
echo "Setup Complete! 🎉"
echo "========================================================================="
echo ""
echo "What you can do now:"
echo ""
echo "1. Start the server:"
echo "   serve run websocket_example:app"
echo ""
echo "2. Test with Hugging Face samples (in another terminal):"
echo "   python quick_test_samples.py"
echo ""
echo "3. Stream from microphone:"
echo "   python client_example.py"
echo ""
echo "4. Transcribe an audio file:"
echo "   python client_example.py your_audio.wav"
echo ""
echo "See QUICKSTART.md for more information."
echo ""

