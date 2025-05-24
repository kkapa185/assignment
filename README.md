# Assignment

## Steps to Start the Application using Docker
Install Docker if not installed: [Install Docker on Ubuntu 22.04](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)

**Step 1:** Check if Docker is running  
```bash
sudo systemctl status docker
```

**Step 2:** Start the application using Docker Compose  
```bash
docker compose up --build -d
```

---

## Running Without Docker
**Requirements:** Python 3.11+ [Download Python](https://www.python.org/downloads/)

**Step 1:** Navigate to the main project directory  
**Step 2:** Create a virtual environment  
```bash
python -m venv venv
```

**Step 3:** Activate the virtual environment and install dependencies  
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Step 4:** Start the FastAPI application  
```bash
uvicorn app.main:app --reload
```

---

## Testing

**To run unit tests:**  
```bash
pytest tests/test_main.py
```

---

## Access API Documentation
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- **Postman Team Collection:**  
  [Postman Workspace Link](https://grey-satellite-599898.postman.co/workspace/My-Workspace~0291e9e1-f5ee-4f6d-8365-81fd4ee31eea/collection/14208817-13fd6ebe-ef54-4e79-8fea-79bef0551ab1?action=share&creator=14208817)

NOTE: Bearer tokens (Access/Refresh) are passed in all API except Register and Login


## APIs implemented
| Status | Method | Endpoint                                             | Type             | Description                                                       |
|----|--------|------------------------------------------------------|------------------|-------------------------------------------------------------------|
| ✅ | POST   | /api/auth/register                                   | Authentication   | Register a new user                                               |
| ✅ | POST   | /api/auth/login                                      | Authentication   | Login and receive an authentication token                         |
| ✅ | POST   | /api/auth/refresh                                    | Authentication   | Refresh an authentication token                                   |
| ✅ | POST   | /api/auth/logout                                     | Authentication   | Invalidate the current token                                      |
| ✅ | POST   | /api/events                                          | Event            | Create a new event                                                |
| ✅ | GET    | /api/events                                          | Event            | List all events the user has access to (with pagination/filtering)|
| ✅ | GET    | /api/events/{id}                                     | Event            | Get a specific event by ID                                        |
| ✅ | PUT    | /api/events/{id}                                     | Event            | Update an event by ID                                             |
| ✅ | DELETE | /api/events/{id}                                     | Event            | Delete an event by ID                                             |
| ✅ | POST   | /api/events/batch                                    | Event            | Create multiple events in a single request                        |
| ✅ | POST   | /api/events/{id}/share                               | Collaboration    | Share an event with other users                                   |
| ✅ | GET    | /api/events/{id}/permissions                         | Collaboration    | List all permissions for an event                                 |
| ✅ | PUT    | /api/events/{id}/permissions/{userId}               | Collaboration    | Update permissions for a user                                     |
| ✅ | DELETE | /api/events/{id}/permissions/{userId}               | Collaboration    | Remove access for a user                                          |
| ✅ | GET    | /api/events/{id}/history/{versionId}                | Version History  | Get a specific version of an event                                |
| ✅ | POST   | /api/events/{id}/rollback/{versionId}               | Version History  | Rollback to a previous version                                    |
| ✅ | GET    | /api/events/{id}/changelog                           | Changelog        | Get a chronological log of all changes to an event                |
| ✅ | GET    | /api/events/{id}/diff/{versionId1}/{versionId2}     | Changelog        | Get a diff between two versions                                   |

