# Project Setup

This project uses Python 3.12 and a virtual environment to manage dependencies. Follow the steps below to set up the development environment using `make` commands.

## Prerequisites

1. **Python 3.12**: If you don’t have it installed, you can download it from the [Python Downloads page](https://www.python.org/downloads/).
2. **Make**: Ensure `make` is installed. It’s commonly available on Linux and macOS. Windows users may need to install it via [Chocolatey](https://chocolatey.org/install) or [Git Bash](https://gitforwindows.org/).

## Setup Instructions

For all Make Commands, if the command doesnt work properly via Make XYZ, then open the Makefile and copy and paste the relevant commands.

1. **Create the Virtual Environment**:
   ```bash
   make setup_venv
   ```
   This command will create a virtual environment in the `venv` directory and then drop you into an interactive shell with the environment activated.

2. **Activate the Virtual Environment (if not already activated)**:
   - You can run:
     ```bash
     make shell
     ```
   This command activates the virtual environment and provides an interactive shell session. Once activated, you’ll see a message confirming that the virtual environment is active.

3. **Install Project Dependencies**:
   With the virtual environment active, install the required packages:
   ```bash
   make install
   ```

3. **Setting up the DB tables**:
   With the virtual environment active, setup the database:
   ```bash
   make setup_db
   ```

4. **Environment Variables**:
   Copy the .env.example into your .env file.
   Replace keys as needed.

## Deactivating the Virtual Environment

When you are done working on the project, you can deactivate the virtual environment by running:
```bash
deactivate
```
OR
```bash
exit
```

# **Ensure All Commands Are Run Inside the Virtual Environment (VENV)**

Before running any commands, make sure the virtual environment (VENV) is active. You can activate it with:
```bash
make shell
```

## Adding Dependencies

If you add new dependencies, update the `requirements.txt` file by freezing the current environment:
```bash
make freeze
```

## Running the Application

To start the application, (ensure DB is setup first) use:
```bash
make run
```
This command will launch the application using Uvicorn in development mode, as specified in the `Makefile`.

## Code formatting + Quality

To ensure code quality and standards, use:
```bash
make style
```

## Running Tests

To run the test suite, use:
```bash
make test
```

## Additional Commands

You can see a list of all available commands by running:
```bash
make help
```

## API Documentation

FastAPI automatically generates interactive API documentation, following the OpenAPI standard. Once the application is running, you can view and explore the API documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)


### Project Structure: Feature-Based Organisation

The project uses a feature-based folder structure, where each core feature resides in its own directory, containing all related files (routes, services, models, etc.). This approach offers key benefits:

- **Encapsulation**: Each feature is self-contained, making it easier to understand and work on independently.
- **Scalability**: New features can be added with minimal impact, allowing the codebase to grow in a modular way.
- **Readability**: The code is organised intuitively, making navigation simpler as the application expands.
- **Maintainability**: Feature-specific tests (e.g., `test_train_times.py`) correspond to their respective feature folders, making the testing process more streamlined.
- **Separation of Concerns**: Each feature handles its own logic, promoting cleaner, more focused code.

## Decision Log / Assumptions / Extra Features

- **Pre-commit Hooks**: 
   - I’ve opted not to add pre-commit hooks at this time. Adding them later is straightforward.

- **Error Handling / Custom Errors**
   - There is room for improvement for custom errors + custom error handling. I've added a custom error exception to show an example of it could be handled, but haven't fully implemented it across the code base.

- **Tests**
   - To save time, I've not added Unit / Integration tests for all parts of the code and haven't aimed for a certain % coverage, however to demonstrate my ability I've unit tested some core functionality that showcases mocking. In a real project I would ensure high coverage of unit tests.

- **Monitoring + Metrics**
   - It would be good to add some form of monitoring to the API + custom metrics. However I have added logging.

- **Configuration Management**:
   - I opted for a JSON file (`config.json`) and environment variables for basic configuration settings. In a production setting, I would consider using a dedicated configuration management tool for handling sensitive information.

- **Dependency Injection**:
   - I have not implemented dependency injection everywhere to keep the codebase simpler for this test, but have shown 1 or 2 examples. In a larger project, I would use dependency injection where possible to better manage external service connectors, making the code more modular and testable.

- **Authentication & Authorisation**:
   - In production, I'd implement token-based authentication (e.g., JWT) to secure endpoints and control access based on user roles.

- **Caching**:
   - Caching works by checking an API requests table. Each API request for data contains a 24hr window. If an API request doesnt exist it will first populate the DB and then utilise data from the DB.

- **DB Migrations / Alembric**:
   - Ideally would use a tool like Alembric to manage DB changes.

- **DB Pooling**:
   - In a real world scenario you would try to use some form of pooling for the DB connections to improve performance and reduce overhead. 

- **Logging**:
   - I’ve included basic logging. In production, I would configure more robust logging, potentially integrating with a centralised logging service (e.g. AWS CloudWatch).

- **Data Validation**:
   - Basic Pydantic models are used for validation, but for a full implementation, I would add more comprehensive validation rules, especially for user inputs.

- **Continuous Integration / Continuous Deployment (CI/CD)**:
   - I have not set up CI/CD pipelines for this test. For production, I would implement CI/CD to automate testing, linting, and deployment using tools such as GitHub Actions or CircleCI.

- **API Versioning**:
   - In a live project, I would add API versioning to ensure backward compatibility and smoother transitions for future changes.


## Config Explanation

```json
"connectors": {
    "train_times_api": {
        "base_url": "https://transportapi.com/v3/uk/train",
        "dev_mode": false,  // When true, uses mock_data_path for API response instead of making a call.
        "mock_data_path": "tests/data/example_response5.json",
        "save_raw_data": false  // When true, every API call made is saved in the api_raw_data folder.
    }
}
```