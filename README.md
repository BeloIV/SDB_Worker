# SDB Worker Project

A team management application with Django backend and React frontend.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SDB_WORKER
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database on port 5432
   - Django backend on port 8000
   - React frontend on port 3000

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Development

### Backend (Django)
- Located in `backend/` directory
- Uses PostgreSQL database
- REST API with Django REST Framework
- CORS enabled for frontend communication

### Frontend (React)
- Located in `frontend/` directory
- React application with modern UI components
- Communicates with Django backend via REST API

### Database
- PostgreSQL 16
- Data persists in Docker volume `postgres_data`

## Environment Variables

The backend automatically uses these default values:
- `POSTGRES_DB=postgres`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_HOST=db`
- `POSTGRES_PORT=5432`
- `DEBUG=True`

## Useful Commands

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and start
docker-compose up --build

# Access backend shell
docker-compose exec backend python manage.py shell

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run migrations manually
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic
```

## Troubleshooting

1. **Database connection issues**: Make sure PostgreSQL container is healthy before backend starts
2. **Port conflicts**: Check if ports 3000, 8000, or 5432 are already in use
3. **Permission issues**: Run `docker-compose down -v` to remove volumes and start fresh

## Project Structure

```
SDB_WORKER/
├── backend/          # Django backend
├── frontend/         # React frontend
├── docker-compose.yaml
└── README.md
```
