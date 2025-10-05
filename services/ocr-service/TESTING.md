# OCR Service Development Testing Guide

## Quick Start

The OCR service is now fully configured for development testing with:

- ✅ **Two-stage processing pipeline** (Preprocessing → OCR Extraction)
- ✅ **Enhanced logging** with colored output and job tracking
- ✅ **Image storage service** with placeholder implementation
- ✅ **RQ worker integration** for async job processing
- ✅ **Webhook authentication** with HMAC signatures
- ✅ **API key authentication** between services

## Starting the Development Server

```bash
cd services/ocr-service

# Start OCR service with RQ worker and enhanced logging
python dev-start.py
```

This will:
1. Check Redis and MongoDB connections
2. Start RQ worker for job processing
3. Start FastAPI server on port 8001
4. Enable enhanced logging with job tracking

## Available Endpoints

- **FastAPI Server**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **RQ Dashboard**: http://localhost:9181 (if running separately)

### Testing Endpoints

```bash
# Health check
curl http://localhost:8001/health

# Submit OCR job (from Node.js API)
curl -X POST "http://localhost:8001/api/v1/jobs/process-invoice" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-ocr-service-key-12345" \
  -d '{
    "image_url": "https://example.com/invoice.jpg",
    "user_id": "test-user-123",
    "message_id": "test-msg-456",
    "webhook_url": "http://localhost:3000/webhook/ocr-complete"
  }'

# Check storage stats
curl http://localhost:8001/images/stats
```

## Testing with LINE Chat Flow

### Expected Flow:
1. **User sends image** to LINE chat
2. **Node.js API receives** webhook from LINE
3. **Node.js API submits** OCR job to Python service
4. **Python service processes** in two stages:
   - Stage 1: Preprocessing (image enhancement)
   - Stage 2: OCR extraction (text recognition)
5. **Python service sends** webhook back to Node.js API
6. **Node.js API responds** to user via LINE

### Log Output to Watch For:

```
🚀 Enhanced development logging configured
[██████████] 100% - DOWNLOADING IMAGE - URL: https://...
[██████████] 100% - PREPROCESSING - Operations: resize, denoise, enhance_contrast
[██████████] 100% - LOADING ENHANCED IMAGE - URL: http://localhost:8001/images/...
[██████████] 100% - OCR_EXTRACTION - PaddleOCR processing
📡 WEBHOOK ✅ SUCCESS - job.completed to http://localhost:3000/... (0.25s)
```

## Development Features

### Enhanced Logging
- **Colored console output** with job tracking
- **Progress bars** for pipeline stages
- **Webhook activity logging** with timing
- **File logging** to `dev-ocr-service.log`

### Job Processing
- **Two-stage pipeline**: Preprocessing → OCR
- **Image storage**: Local filesystem with URL serving
- **Redis queues**: Separate queues for each stage
- **Job metadata**: Progress tracking and error handling

### Authentication
- **API key**: `dev-ocr-service-key-12345`
- **Webhook signatures**: HMAC-SHA256 with secret `dev-webhook-secret-67890`
- **CORS enabled** for development

## Environment Configuration

See `.env.dev` for all configuration options:

```bash
# Key settings for development
NODE_ENV=development
REDIS_URL=redis://localhost:6379
MONGODB_URI=mongodb://localhost:27017/ocr_results
SERVICE_API_KEY=dev-ocr-service-key-12345
WEBHOOK_SECRET=dev-webhook-secret-67890
IMAGE_STORAGE_PATH=/tmp/ocr_images
```

## Troubleshooting

### Common Issues

1. **Redis connection failed**
   ```bash
   # Start Redis server
   redis-server
   ```

2. **MongoDB connection failed**
   ```bash
   # Start MongoDB (optional for basic testing)
   mongod --dbpath /tmp/mongodb
   ```

3. **Port 8001 already in use**
   ```bash
   # Find and kill process
   lsof -ti:8001 | xargs kill -9
   ```

4. **RQ worker not processing jobs**
   ```bash
   # Check RQ dashboard at http://localhost:9181
   # Or manually start worker:
   rq worker --with-scheduler
   ```

### Debug Commands

```bash
# Test worker imports
python -c "from app.workers.preprocessing_worker import preprocess_invoice_image; print('OK')"
python -c "from app.workers.ocr_extraction_worker import extract_invoice_text; print('OK')"

# Test Redis connection
python -c "from app.database.redis_client import get_redis_connection; conn = get_redis_connection(); conn.ping(); print('Redis OK')"

# Check log file
tail -f dev-ocr-service.log
```

## Next Steps

1. **Start the development server**: `python dev-start.py`
2. **Ensure Node.js API** is configured to send jobs to OCR service
3. **Send test image** through LINE chat
4. **Monitor logs** for processing pipeline
5. **Check webhook** delivery to Node.js API

The service is ready for testing the complete LINE chat integration!