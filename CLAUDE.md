# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Invoice OCR system that integrates PaddleOCR with LINE Messaging API for processing Thai invoices. The system uses a monorepo architecture with pnpm workspaces, featuring a Vue.js SPA frontend with LINE LIFF for camera capture, Node.js/Hono for the main API, and Python/FastAPI for document processing.

## Monorepo Structure

This project uses **pnpm workspaces** for managing multiple packages in a monorepo structure.

## Architecture

### Service Components

1. **Frontend Application (Vue.js + DaisyUI + LINE LIFF)**
   - Location: `packages/web/`
   - Vue 3 SPA with Composition API
   - **DaisyUI v4** component library with:
     - 30+ semantic component classes
     - Multiple built-in themes
     - No JavaScript required (pure CSS)
     - Fully customizable with CSS variables
   - TailwindCSS v4 (base for DaisyUI)
   - LINE LIFF SDK for authentication and camera access
   - Real-time camera capture with guidelines
   - Image preprocessing (skew correction, distortion removal, perspective warping)
   - OpenCV.js for image manipulation
   - Pica for high-quality image resizing
   - **OCR Result Review and Correction Interface**:
     - Display OCR results with confidence scores
     - Highlight low-confidence fields for user review
     - Editable forms for correcting extracted data
     - Save corrected results via API

1.5. **Admin Dashboard (Vue.js + DaisyUI)**
   - Location: `packages/admin/`
   - Vue 3 SPA with Composition API and TypeScript
   - **TailwindCSS v4 with DaisyUI v4** for modern UI components
   - **Protected Routes** with authentication guards
   - **Features**:
     - Admin authentication with JWT tokens
     - Responsive layout with collapsible sidebar
     - Dashboard overview with system statistics
     - User management (LINE users)
     - Invoice/OCR results management
     - Job queue monitoring
     - Message history management
     - System settings and configuration
     - Multi-theme support (light, dark, corporate, business, custom admin theme)
   - **Authentication Flow**:
     - JWT-based admin authentication
     - Protected routes requiring valid tokens
     - Automatic token validation and refresh
     - Session persistence with localStorage

2. **Main API Service (Node.js + Hono)**
   - Location: `packages/api/`
   - Handles LINE webhook events
   - Manages user authentication and sessions
   - Routes document processing requests to Python service
   - Connects to PostgreSQL for user/message data
   - Serves image preprocessing endpoints for web client
   - **Endpoints for OCR result correction**:
     - `GET /ocr-results/:id` - Fetch results for review
     - `PUT /ocr-results/:id/corrections` - Save user corrections
     - `GET /ocr-results/:id/review-link` - Generate LIFF review URL

3. **OCR Processing Service (Python + FastAPI)**
   - Location: `services/ocr-service/`
   - **Two-Stage Processing Pipeline**:
     - Stage 1: Image Preprocessing Job
     - Stage 2: OCR Extraction Job
   - Implements PaddleOCR for Thai text extraction
   - Uses RQ (Redis Queue) for async processing
   - **RQ Dashboard Integration** for queue monitoring
   - Processes invoices and categorizes them
   - Stores results in MongoDB
   - **Returns confidence scores for each field**
   - Tracks user corrections for model improvement

4. **Shared Libraries**
   - Location: `packages/shared/`
   - Common TypeScript types and utilities
   - Shared validation schemas
   - Database models
   - Image processing utilities

5. **Database Layer**
   - PostgreSQL: User data, LINE messages, authentication, correction history
   - MongoDB:
     - Raw OCR output (full text, text blocks with bounding boxes)
     - Structured invoice data
     - Confidence scores
     - User corrections
     - Processing metadata
   - Redis: Job queue for async processing, session management for review links

### Key Integration Points

- **Web Flow**: User opens LIFF app → Camera capture → Image preprocessing → Send to LINE chat
- **Unified Flow**: All images (from web or direct chat) arrive at webhook → Main API
- Main API queues OCR job → Redis/RQ
- FastAPI worker processes job → PaddleOCR
- Results stored in MongoDB → Retrieved by Main API
- Response sent back through LINE API (visible in chat for both flows)

## Development Commands

### Monorepo Management (pnpm)
```bash
# Install pnpm globally (if not installed)
npm install -g pnpm

# Install all dependencies for all packages
pnpm install

# Install dependencies for specific workspace
pnpm --filter @invoice-ocr/api install
pnpm --filter @invoice-ocr/web install
pnpm --filter @invoice-ocr/shared install

# Run commands across workspaces
pnpm -r build  # Build all packages
pnpm -r test   # Run tests in all packages
pnpm -r lint   # Lint all packages

# Run dev servers concurrently
pnpm dev  # Runs all dev scripts in parallel
```

### API Service (packages/api)
```bash
# Development with hot reload
pnpm --filter @invoice-ocr/api dev

# Build
pnpm --filter @invoice-ocr/api build

# Run tests
pnpm --filter @invoice-ocr/api test
pnpm --filter @invoice-ocr/api test:watch

# Linting
pnpm --filter @invoice-ocr/api lint
pnpm --filter @invoice-ocr/api lint:fix

# Type checking
pnpm --filter @invoice-ocr/api typecheck
```

### Frontend Application (packages/web)
```bash
# Development server with hot reload
pnpm --filter @invoice-ocr/web dev

# Build for production
pnpm --filter @invoice-ocr/web build

# Preview production build
pnpm --filter @invoice-ocr/web preview

# Run tests
pnpm --filter @invoice-ocr/web test
pnpm --filter @invoice-ocr/web test:e2e

# Linting
pnpm --filter @invoice-ocr/web lint
pnpm --filter @invoice-ocr/web lint:fix

# Type checking
pnpm --filter @invoice-ocr/web typecheck
```

### Admin Dashboard (packages/admin)
```bash
# Development server with hot reload (runs on port 5174)
pnpm --filter @invoice-ocr/admin dev
# or
pnpm dev:admin

# Build for production
pnpm --filter @invoice-ocr/admin build

# Preview production build
pnpm --filter @invoice-ocr/admin preview

# Type checking
pnpm --filter @invoice-ocr/admin typecheck

# Linting
pnpm --filter @invoice-ocr/admin lint
```

### Shared Package (packages/shared)
```bash
# Build
pnpm --filter @invoice-ocr/shared build

# Watch mode for development
pnpm --filter @invoice-ocr/shared dev

# Run tests
pnpm --filter @invoice-ocr/shared test

# Type checking
pnpm --filter @invoice-ocr/shared typecheck
```

### Python OCR Service
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r services/ocr-service/requirements.txt

# Run FastAPI server
cd services/ocr-service
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Run RQ worker
cd services/ocr-service
rq worker --with-scheduler

# Run RQ Dashboard (Queue Monitoring)
rq-dashboard --redis-url redis://localhost:6379
# Access at http://localhost:9181
# Features:
# - Real-time queue statistics
# - Job inspection and management
# - Failed job retry/deletion
# - Worker monitoring

# Run tests
cd services/ocr-service
pytest
pytest -v  # verbose
pytest tests/test_ocr.py::specific_test  # run specific test

# Linting
cd services/ocr-service
ruff check .
black .
```

### Docker Commands
```bash
# Build and run all services
docker-compose up --build

# Run specific service
docker-compose up api
docker-compose up ocr-service
docker-compose up rq-dashboard

# View logs
docker-compose logs -f api
docker-compose logs -f ocr-service
docker-compose logs -f rq-dashboard

# Access services
# - API: http://localhost:3000
# - OCR Service: http://localhost:8001
# - RQ Dashboard: http://localhost:9181
```

### Database Setup
```bash
# PostgreSQL migrations (using Prisma)
pnpm --filter @invoice-ocr/api prisma:migrate
pnpm --filter @invoice-ocr/api prisma:generate
pnpm --filter @invoice-ocr/api prisma:studio  # Open Prisma Studio

# MongoDB initialization
pnpm --filter @invoice-ocr/api db:seed
```

## Environment Configuration

### Required Environment Variables

**Frontend Application (.env)**
```
VITE_LIFF_ID=
VITE_API_URL=http://localhost:3000
VITE_LINE_CHANNEL_ID=
```

**API Service (.env)**
```
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
DATABASE_URL=postgresql://user:password@localhost:5432/invoice_db
MONGODB_URI=mongodb://localhost:27017/ocr_results
OCR_SERVICE_URL=http://localhost:8001
REDIS_URL=redis://localhost:6379
```

**OCR Service (.env)**
```
MONGODB_URI=mongodb://localhost:27017/ocr_results
REDIS_URL=redis://localhost:6379
PADDLEOCR_LANG=th
RQ_DASHBOARD_REDIS_URL=redis://localhost:6379
RQ_DASHBOARD_PORT=9181
```

## Project Structure Guidelines

```
invoice-ocr/
├── packages/                 # pnpm workspace packages
│   ├── web/                 # Vue.js frontend
│   │   ├── src/
│   │   │   ├── components/  # Vue components
│   │   │   │   ├── CameraCapture.vue
│   │   │   │   ├── ImagePreview.vue
│   │   │   │   └── ui/         # DaisyUI components
│   │   │   ├── views/       # Page components
│   │   │   │   ├── CameraCapture.vue  # Invoice capture
│   │   │   │   └── ReviewCorrection.vue  # OCR result review
│   │   │   ├── composables/ # Vue composables
│   │   │   ├── stores/      # Pinia stores
│   │   │   ├── utils/       # Frontend utilities
│   │   │   │   ├── camera.ts    # Camera capture logic
│   │   │   │   ├── opencv.ts    # OpenCV image processing
│   │   │   │   └── liff.ts      # LINE LIFF integration
│   │   │   ├── styles/      # TailwindCSS v4 styles
│   │   │   └── App.vue
│   │   ├── public/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts  # With DaisyUI plugin
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── admin/               # Admin dashboard
│   │   ├── src/
│   │   │   ├── views/       # Page components
│   │   │   │   ├── Login.vue       # Admin login
│   │   │   │   ├── Dashboard.vue   # Overview dashboard
│   │   │   │   ├── Users.vue       # User management
│   │   │   │   ├── Invoices.vue    # Invoice management
│   │   │   │   ├── Jobs.vue        # Job queue monitoring
│   │   │   │   ├── Messages.vue    # Message management
│   │   │   │   ├── Settings.vue    # System settings
│   │   │   │   └── NotFound.vue    # 404 page
│   │   │   ├── layouts/     # Layout components
│   │   │   │   └── DefaultLayout.vue  # Main layout with sidebar
│   │   │   ├── components/  # Reusable components
│   │   │   │   ├── Sidebar.vue     # Navigation sidebar
│   │   │   │   └── Header.vue      # Top header
│   │   │   ├── router/      # Vue Router configuration
│   │   │   │   └── index.ts        # Routes with auth guards
│   │   │   ├── stores/      # Pinia stores
│   │   │   │   └── auth.ts         # Authentication store
│   │   │   ├── api/         # API client
│   │   │   ├── App.vue
│   │   │   ├── main.ts
│   │   │   └── style.css    # TailwindCSS imports
│   │   ├── public/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts  # Custom admin theme
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── api/                 # Main API service
│   │   ├── src/
│   │   │   ├── routes/      # API routes
│   │   │   ├── services/    # Business logic
│   │   │   ├── models/      # Database models
│   │   │   └── middleware/  # Hono middleware
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── shared/             # Shared utilities and types
│       ├── src/
│       │   ├── types/       # TypeScript type definitions
│       │   ├── schemas/     # Validation schemas
│       │   └── utils/       # Shared utilities
│       ├── package.json
│       └── tsconfig.json
├── services/                # Non-JS services
│   └── ocr-service/        # Python FastAPI service
│       ├── app/
│       │   ├── api/        # FastAPI routes
│       │   ├── core/       # Core OCR logic
│       │   ├── models/     # Pydantic models
│       │   └── workers/    # RQ workers
│       │       ├── preprocessing.py  # Image enhancement job
│       │       └── ocr_extraction.py # PaddleOCR job
│       ├── requirements.txt
│       └── main.py
├── pnpm-workspace.yaml      # pnpm workspace configuration
├── package.json             # Root package.json
├── docker-compose.yml
├── .env.example
└── turbo.json              # Turborepo config (optional)
```

### pnpm Workspace Configuration

**pnpm-workspace.yaml:**
```yaml
packages:
  - 'packages/*'
```

**Root package.json:**
```json
{
  "name": "invoice-ocr",
  "private": true,
  "scripts": {
    "dev": "pnpm -r --parallel dev",
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "lint": "pnpm -r lint",
    "typecheck": "pnpm -r typecheck"
  },
  "devDependencies": {
    "turbo": "^1.10.0"
  }
}
```

## LINE Integration

### LINE Messaging API
- Webhook endpoint: `POST /webhook` in main API
- Handle image messages for invoice processing
- Rich menu for user interactions
- Quick replies for invoice categorization confirmation

### LINE LIFF (Frontend)
- Initialize LIFF in Vue app
- Access device camera through LIFF API
- User authentication via LINE Login
- Send preprocessed images to chat using `liff.sendMessages()`
- Include metadata for web-originated images

## Invoice Processing Pipeline

### Web Application Flow (Lightweight Preprocessing + Send to Chat)
1. User opens LIFF app in LINE
2. Camera interface with capture guidelines displayed
3. User captures invoice image
4. **Client-side lightweight preprocessing** (fast, real-time):
   - Auto-detect document edges
   - Perspective correction (deskew/dewarp)
   - Basic contrast adjustment
   - Resolution optimization with Pica
5. Processed image sent to LINE chat using LIFF SDK:
   ```javascript
   liff.sendMessages([{
     type: 'image',
     originalContentUrl: processedImageUrl,
     previewImageUrl: thumbnailUrl
   }])
   ```
6. Image appears in chat and triggers webhook

### Unified Processing Flow (Webhook → Backend Jobs)
1. Main API receives webhook event (from web app or direct chat)
2. Image downloaded from LINE servers
3. Metadata checked for frontend preprocessing flag
4. **Two-Stage Backend Job Queue (Heavy Processing)**:
   - **Stage 1: Server-side Preprocessing Job**
     - Image sharpening using OpenCV
     - Advanced denoising (bilateral filtering)
     - Adaptive thresholding for text enhancement
     - Histogram equalization
     - Morphological operations (erosion/dilation)
     - Binarization (Otsu's method)
     - Text region detection
     - Saves enhanced image to storage
   - **Stage 2: OCR Extraction Job**
     - Uses enhanced image from Stage 1
     - PaddleOCR extracts Thai text with confidence scores
     - Multiple pass extraction for low confidence areas
5. Text parsed for invoice fields (vendor, amount, date, items)
6. Invoice categorized (expense type, tax category)
7. Results stored in MongoDB with confidence metrics
8. **Confidence-based Response**:
   - High confidence (>80%): Direct response in LINE chat
   - Low confidence (<80%): Send review link to LIFF app for correction
9. User receives response in LINE chat

### OCR Result Correction Flow (Low Confidence)
1. User receives message with review link in LINE chat
2. Link opens LIFF app with OCR results pre-loaded
3. Low-confidence fields highlighted in red/yellow
4. User reviews and corrects extracted data:
   - Edit vendor name
   - Adjust amounts
   - Correct dates
   - Modify line items
5. User submits corrections
6. Corrected data saved to MongoDB with user_verified flag
7. Confirmation sent back to LINE chat
8. System learns from corrections for future improvements

## Image Processing Guidelines

### Camera Capture UI
- Overlay guide frame for invoice alignment
- Real-time edge detection feedback
- Auto-capture when document is properly aligned
- Manual capture override option

### Image Preprocessing Layers

#### Frontend (Lightweight - Real-time)
```javascript
// OpenCV.js operations (minimal for performance)
- cv.Canny() for edge detection
- cv.findContours() for document detection
- cv.getPerspectiveTransform() for perspective correction
- cv.warpPerspective() for deskewing

// Pica operations
- High-quality image resizing
- Maintain aspect ratio
- Optimize file size for upload
```

#### Backend (Heavy Processing - Python/OpenCV)
```python
# Stage 1: Preprocessing Job
- cv2.bilateralFilter() - Advanced noise reduction
- cv2.unsharp_mask() - Sharpening for blurry text
- cv2.adaptiveThreshold() - Local contrast enhancement
- cv2.morphologyEx() - Text region cleaning
- cv2.threshold(cv2.THRESH_OTSU) - Optimal binarization

# Stage 2: OCR Job
- PaddleOCR with Thai language model
- Multi-angle text detection
- Confidence scoring per field
```

## Thai Language Considerations

- Ensure PaddleOCR is configured with Thai language model
- Handle Thai date formats (Buddhist calendar)
- Support Thai number formats and currency (บาท)
- Invoice field mapping for common Thai invoice layouts

## Testing Approach

### Frontend Tests
- Unit tests for image processing functions
- Component tests for camera capture UI
- E2E tests for complete capture flow
- Mock LIFF API for testing

### Backend Tests
- Unit tests for OCR text extraction functions
- Integration tests for LINE webhook handling
- Mock PaddleOCR responses for consistent testing
- Test various Thai invoice formats

## Frontend Dependencies

### Core Libraries
- Vue 3 with Composition API
- Vite for build tooling
- Pinia for state management
- Vue Router for navigation

### UI/Styling
- TailwindCSS v4
- DaisyUI v4 (component library)
- Heroicons for icons

### Image Processing
- OpenCV.js for computer vision operations
- Pica for image resizing
- Canvas API for basic operations

### LINE Integration
- @line/liff SDK
- axios for API communication

## OCR Confidence and Correction System

### Confidence Thresholds
```javascript
const CONFIDENCE_LEVELS = {
  HIGH: 0.8,      // >80% - Auto-accept
  MEDIUM: 0.6,    // 60-80% - Highlight for review
  LOW: 0.0        // <60% - Require correction
}
```

### MongoDB Schema for OCR Results
```javascript
{
  _id: ObjectId,
  invoice_id: String,
  user_id: String,
  original_image_url: String,
  processed_image_url: String,
  enhanced_image_url: String,  // After backend preprocessing

  // Raw OCR output from PaddleOCR
  raw_ocr_result: {
    full_text: String,          // Complete extracted text
    text_blocks: [{
      text: String,
      confidence: Number,
      bbox: [Number, Number, Number, Number],  // Bounding box coordinates
      polygon: [[Number, Number]],              // Text region polygon
    }],
    processing_time_ms: Number,
    paddle_version: String,
    model_used: String
  },

  // Structured parsed results
  ocr_results: {
    vendor: { value: String, confidence: Number },
    invoice_number: { value: String, confidence: Number },
    date: { value: Date, confidence: Number },
    total_amount: { value: Number, confidence: Number },
    line_items: [{
      description: { value: String, confidence: Number },
      amount: { value: Number, confidence: Number }
    }]
  },

  overall_confidence: Number,
  user_corrections: {
    corrected_at: Date,
    corrected_by: String,
    corrections: Object,
    user_verified: Boolean
  },

  processing_metadata: {
    frontend_preprocessed: Boolean,
    backend_preprocessing_job_id: String,
    ocr_job_id: String,
    total_processing_time_ms: Number
  },

  created_at: Date,
  updated_at: Date
}
```

### Review Form Components (Using DaisyUI)
- **ConfidenceIndicator.vue** - Visual confidence display using DaisyUI badges and progress
- **EditableField.vue** - DaisyUI form controls with validation states
- **LineItemsEditor.vue** - Dynamic form using DaisyUI table and inputs
- **ReviewSummary.vue** - Before/after comparison with DaisyUI cards

### DaisyUI Configuration
```javascript
// tailwind.config.ts
export default {
  content: ['./src/**/*.{vue,js,ts}'],
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      'light',
      'dark',
      'cupcake',  // Soft pastel theme
      {
        invoice: {  // Custom theme for invoice app
          'primary': '#1E40AF',
          'secondary': '#64748B',
          'accent': '#10B981',
          'neutral': '#1F2937',
          'base-100': '#FFFFFF',
          'info': '#3ABFF8',
          'success': '#36D399',
          'warning': '#FBBD23',
          'error': '#F87272',
        }
      }
    ],
    darkTheme: 'dark',
    base: true,
    styled: true,
    utils: true,
    prefix: '',
    logs: true,
    themeRoot: ':root'
  }
}
```

## Queue Monitoring with RQ Dashboard

### Features
- **Queue Overview**: Real-time statistics for all queues (default, preprocessing, ocr)
- **Job Management**:
  - View pending, started, finished, and failed jobs
  - Inspect job details, arguments, and results
  - Retry failed jobs
  - Delete stuck jobs
- **Worker Monitoring**:
  - Active worker status
  - Current job processing
  - Worker performance metrics
- **Job History**:
  - Execution times
  - Success/failure rates
  - Processing bottlenecks identification

### Python Dependencies
```txt
# Add to services/ocr-service/requirements.txt
rq==1.15.1
rq-dashboard==0.6.1
redis==5.0.0
```

### Docker Compose Service
```yaml
rq-dashboard:
  image: eoranged/rq-dashboard
  ports:
    - "9181:9181"
  environment:
    - RQ_DASHBOARD_REDIS_URL=redis://redis:6379
  depends_on:
    - redis
```