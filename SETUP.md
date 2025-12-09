# ResQ AI - Setup Guide

## Environment Configuration

This application uses environment variables for configuration. Follow these steps to set up your environment:

### 1. Create Your .env File

Copy the example environment file and configure it with your credentials:

```bash
cp env.example .env
```

### 2. Configure Required Variables

Open the `.env` file and set the following required variables:

#### AWS Configuration (Required for S3 operations)
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
```

#### Application Configuration (Optional)
```
APP_ENV=development  # Options: development, staging, production
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 3. Verify Your Setup

The application will automatically load environment variables on startup. You can verify your AWS credentials are configured correctly by checking if S3 operations work.

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | us-east-1 | AWS region for S3 operations |
| `AWS_ACCESS_KEY_ID` | Yes | - | AWS access key for authentication |
| `AWS_SECRET_ACCESS_KEY` | Yes | - | AWS secret key for authentication |
| `AWS_BUCKET_NAME` | No | - | Default S3 bucket name (optional) |
| `APP_ENV` | No | development | Application environment |
| `HOST` | No | 0.0.0.0 | Server host address |
| `PORT` | No | 8000 | Server port number |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Security Notes

⚠️ **IMPORTANT**:
- Never commit your `.env` file to version control
- The `.env` file is already included in `.gitignore`
- Keep your AWS credentials secure
- Rotate credentials regularly
- Use IAM roles with minimal required permissions

### Using the Config Module

The application provides a centralized config module for accessing environment variables:

```python
from app.utils.config import config

# Access configuration values
print(config.AWS_REGION)
print(config.APP_ENV)

# Check if running in development
if config.is_development():
    print("Running in development mode")

# Validate AWS credentials
if config.validate_aws_credentials():
    print("AWS credentials are configured")
```

## Running the Application

After setting up your `.env` file:

```bash
# Activate your virtual environment
source venv/bin/activate  # On Unix/macOS
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
# or
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000` by default.

## Docker Setup

If you're using Docker, you can pass environment variables through:

1. **Docker Compose** - Add your `.env` file reference in `docker-compose.yml`
2. **Docker Run** - Use the `--env-file` flag:
   ```bash
   docker run --env-file .env your-image-name
   ```

## Troubleshooting

### Missing Environment Variables

If you see errors about missing AWS credentials:
1. Check that your `.env` file exists in the project root
2. Verify all required variables are set
3. Make sure you're not using quotes around values (unless they contain spaces)
4. Restart your application after changing `.env` values

### AWS Credentials Not Working

1. Verify your AWS credentials are valid
2. Check that your IAM user has the necessary S3 permissions
3. Ensure the AWS region matches where your S3 bucket is located
4. Test credentials using AWS CLI: `aws s3 ls`
