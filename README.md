# ResQ AI Service

ResQ AI Service is a **FastAPI** microservice responsible for AI-driven media analysis and text summarization within the ResQ platform. This service processes images and text data to detect objects and generate summaries, enhancing safety monitoring and report generation.

## 🏗 Tech Stack

- **FastAPI** – High-performance web framework
- **Python** – Core language
- **YOLOv8** – AI model for object detection in images
- **Sumy** – Text summarization library
- **NLTK** – Natural language processing
- **Pillow** – Image processing
- **Boto3** – AWS S3 integration for media storage
- **Pydantic** – Data validation
- **Docker** – Containerization

## 🚀 Features

- **Image Analysis** – Object detection using YOLOv8
- **Text Summarization** – Using LSA algorithm via Sumy
- **S3 Integration** – Media file storage and retrieval
- **Structured API** – Clear API endpoints and response models
- **Extensible Architecture** – Support for future media types (video/audio)

## 🛠️ API Endpoints

- **POST /process-report-media/** – Process and analyze images from S3
- **POST /process-report-text-content/** – Summarize text content

## 🧩 Project Structure

- **app/modules/** – Core functionality modules (YOLO, Sumy, S3)
- **app/services/** – Processing services for different media types
- **app/controllers/** – API endpoint definitions
- **app/schema/** – Data models using Pydantic
- **app/utils/** – Helper utilities and constants

## 🏃 Quick Start

### Using Makefile (Recommended)

This project includes a Makefile with convenient shortcuts for all common tasks:

```bash
# First time setup
make quick-start              # Complete setup
source venv/bin/activate      # Activate virtual environment
# Edit .env with your AWS credentials

# Start development
make dev                      # Run with auto-reload

# See all available commands
make help
```

### Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
# Edit .env with your credentials

# 4. Run the server
uvicorn app.main:app --reload
```

## 📝 Available Make Commands

| Command | Description |
|---------|-------------|
| `make dev` | Run development server with auto-reload |
| `make run` | Run production server |
| `make lint` | Check code quality with pylint |
| `make format` | Auto-format code with black |
| `make clean` | Remove cache files |
| `make docker-build` | Build Docker image |
| `make docker-up` | Start with Docker Compose |
| `make health` | Check if server is running |
| `make info` | Show project information |

For complete command documentation, see [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) or [README_COMMANDS.md](README_COMMANDS.md)

## ⚙️ Configuration

The application uses environment variables for configuration. See `env.example` for all available options:

- **AWS_REGION** – AWS region for S3
- **AWS_ACCESS_KEY_ID** – AWS access key
- **AWS_SECRET_ACCESS_KEY** – AWS secret key
- **APP_ENV** – Environment (development/production)
- **HOST** – Server host (default: 0.0.0.0)
- **PORT** – Server port (default: 8000)

## 🐳 Docker Support

```bash
# Build and run with Docker Compose
make docker-build
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## 🧪 Development Workflow

```bash
# Start development server
make dev

# Before committing
make format              # Format code
make lint                # Check for issues

# Clean up
make clean              # Remove cache files
```
