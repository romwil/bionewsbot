# BioNewsBot Frontend

A modern, responsive web application for monitoring and analyzing life sciences companies, built with Next.js 14, TypeScript, and Chakra UI.

## Features

### 🏢 Company Management
- Add, edit, and delete companies
- Track company status (active, paused, archived)
- View detailed company profiles
- Monitor multiple companies simultaneously

### 📊 Insights Dashboard
- Real-time insights feed
- Advanced filtering by type, sentiment, and flags
- Detailed insight views with metadata
- Export capabilities

### 🔍 Analysis Engine
- Run comprehensive analysis on companies
- Track analysis progress in real-time
- View detailed results and logs
- Schedule automated analysis runs

### ⚙️ System Configuration
- Manage API keys securely
- Configure notification preferences
- User management and role-based access
- System-wide settings

### 🎨 User Experience
- Dark/Light theme support
- Responsive design for all devices
- Real-time updates via WebSocket
- Intuitive navigation

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: Chakra UI
- **State Management**: 
  - React Query (server state)
  - Zustand (client state)
- **Forms**: React Hook Form
- **HTTP Client**: Axios
- **Charts**: Chart.js
- **Date Handling**: date-fns
- **Authentication**: JWT tokens

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Login page
│   ├── dashboard/         # Dashboard page
│   ├── companies/         # Companies management
│   ├── insights/          # Insights feed
│   ├── analysis/          # Analysis runs
│   └── settings/          # Settings page
├── components/            # Reusable components
│   ├── layout/           # Layout components
│   ├── dashboard/        # Dashboard widgets
│   ├── companies/        # Company components
│   ├── insights/         # Insight components
│   └── analysis/         # Analysis components
├── lib/                   # Utilities and API
│   ├── api/              # API client modules
│   ├── hooks/            # Custom React hooks
│   └── utils/            # Helper functions
├── providers/            # Context providers
├── store/                # Zustand stores
└── types/                # TypeScript types
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

1. Clone the repository:
```bash
cd /root/bionewsbot/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env.local
```

4. Update environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Key Components

### Authentication
- JWT-based authentication
- Protected routes using middleware
- Automatic token refresh
- Role-based UI elements

### Data Management
- React Query for server state caching
- Optimistic updates for better UX
- Real-time updates via WebSocket
- Efficient pagination and filtering

### UI/UX Features
- Responsive design with mobile support
- Dark/light theme toggle
- Loading states and error handling
- Toast notifications for user feedback
- Keyboard shortcuts for power users

## API Integration

The frontend integrates with the FastAPI backend through:

- RESTful API endpoints
- WebSocket for real-time updates
- JWT authentication headers
- Standardized error handling

## Docker Support

Build and run with Docker:

```bash
docker build -t bionewsbot-frontend .
docker run -p 3000:3000 bionewsbot-frontend
```

## Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Add tests for new features
4. Update documentation as needed

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.
