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
