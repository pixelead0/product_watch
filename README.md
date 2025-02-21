# Product Watch

Product Watch is a comprehensive product management and visit tracking system implemented in Python using the Django Ninja framework. It follows software development best practices and clean architecture principles to ensure maintainability, scalability, and robustness.

## Features

- **Product Management**: Full CRUD functionality for managing products, including creating, updating, and deleting products. Accessible only to admin users.
- **Product Viewing**: Anonymous users can view products and their details without authentication.
- **Visit Tracking**: The system tracks visits from anonymous users to product pages, storing information such as IP address (hashed for privacy), user agent, and session data.
- **Analytics and Reporting**: Admins can access various analytics and reports, including popular products, unique visitors, average visit duration, and daily visit stats.
- **Asynchronous Notifications**: The system sends email notifications to admins for important events such as new product creations and updates. Notifications are processed asynchronously using Celery.

## Tech Stack

- **Backend**: Python with Django Ninja web framework
- **Primary Database**: PostgreSQL for storing product, visit, and user data
- **Cache and Session Storage**: Redis for caching and managing user sessions
- **Messaging**: SendGrid (or similar service) for sending transactional emails
- **Containerization**: Docker and Docker Compose for easy development and deployment
- **Dependency Management**: Poetry for managing Python dependencies and virtual environments
- **API Documentation**: OpenAPI (Swagger) for generating interactive API documentation

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/pixelead0/product-watch.git
   ```

2. Install dependencies using Poetry:
   ```
   cd product-watch
   poetry install
   ```

3. Set up environment variables by creating a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```
   Update the values in the `.env` file according to your setup.

4. Run database migrations:
   ```
   poetry run python manage.py migrate
   ```

5. Start the development server:
   ```
   poetry run python manage.py runserver
   ```

The application should now be accessible at `http://localhost:8000`.

## Running with Docker

1. Make sure you have Docker and Docker Compose installed on your system.

2. Build and start the containers:
   ```
   docker-compose up -d
   ```

3. Run database migrations in the `api` container:
   ```
   docker-compose exec api python manage.py migrate
   ```

The API should now be available at `http://localhost:8000/api/`.

## Running Tests

To run the test suite with coverage, use the following command:

```
poetry run pytest --cov=src --cov-report=html
```

This will run all tests and generate a coverage report in the `htmlcov` directory.

## Documentation

Detailed documentation for the project can be found in the `docs` directory:

- [API Documentation](docs/api.md): Comprehensive documentation of API endpoints, request/response formats, and authentication requirements.
- [Architecture Overview](docs/architecture.md): High-level overview of the system architecture, including key components and their interactions.
- [Database Schema](docs/database.md): Description of the database schema, tables, fields, indexes, and entity relationships.
- [Authentication Flow](docs/jwt-auth.md): Detailed explanation of the JWT-based authentication and authorization flow.
- [Visit Tracking Flow](docs/visit-tracking.md): In-depth description of the visit tracking process, including sequence diagrams and key components.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate and maintain code coverage.


## License


This project is licensed under the [GPLv3](LICENSE)