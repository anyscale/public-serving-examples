# NLP Processing Pipeline Frontend

A modern React-based frontend for interacting with the FastAPI NLP Processing Pipeline.

## Features

- **Authentication** with JWT tokens
- **Sentiment Analysis** to determine text emotional tone
- **Named Entity Recognition** to extract people, places, organizations, etc.
- **Text Classification** to categorize text into custom labels
- **Streaming Analysis Demo** using Server-Sent Events (SSE)
- **WebSocket Real-time Communication** for instant NLP processing
- **Responsive Design** that works on desktop and mobile

## Technologies Used

- React 19
- TypeScript
- React Router for routing
- React Query for data fetching
- TailwindCSS for styling
- Axios for API requests
- DaisyUI components
- Server-Sent Events for streaming
- WebSockets for real-time communication

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation and Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. The application will be available at [http://localhost:3000](http://localhost:3000)

## Usage

### Authentication

The application uses JWT token-based authentication:
- Demo credentials are provided on the login page
- Username: `demo`, Password: `password`
- Admin access: Username: `admin`, Password: `password`

### API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api/v1`.
Make sure the backend server is running before using the frontend.

### Features Overview

1. **Dashboard**: View system status and access all features
2. **Sentiment Analysis**: Analyze the emotional tone of text
3. **Named Entity Recognition**: Extract entities from text with confidence filtering
4. **Text Classification**: Classify text using predefined or custom labels
5. **Streaming Demo**: See real-time analysis of longer text chunks
6. **WebSocket Demo**: Experience bi-directional communication

## Development

### Project Structure

- `/src`
  - `/api` - API client and utilities
  - `/components` - Reusable UI components
  - `/contexts` - React context providers (auth, etc.)
  - `/pages` - Main page components
  - `/utils` - Helper functions and utilities

### Adding New Features

To add a new feature:
1. Create any necessary API methods in `/src/api/apiClient.ts`
2. Add a new page component in `/src/pages`
3. Add a route in `App.tsx`
4. Add a navigation link in `Sidebar.tsx`

## Build for Production

To create a production build:

```bash
npm run build
```

The build output will be in the `build` directory, ready to be served.
