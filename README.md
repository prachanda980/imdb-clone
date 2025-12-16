# IMDb Clone API 🎬

A scalable, high-performance RESTful API for a movie database platform. Built with Django Rest Framework, optimized with Redis caching, and capable of handling background tasks via Celery.

## 🚀 Key Features

* **Authentication:** Custom User Model with JWT (Access/Refresh tokens).
* **Database Architecture:** Complex relationships handling Movies, Genres, Actors, Directors, and Crew roles.
* **Performance:**
    * **Redis Caching:** Sub-millisecond response times for movie lists.
    * **Database Optimization:** `prefetch_related` to eliminate N+1 query problems.
    * **Signals:** Auto-calculation of ratings and review counts to reduce read-time computation.
* **Background Tasks:** Celery + Redis for asynchronous welcome emails.
* **Security:** Robust validation for file uploads (size/type) and permission classes (Admin vs. User).

## 🛠 Tech Stack

* **Backend:** Python 3.10+, Django 5.0, Django REST Framework
* **Database:** PostgreSQL (or SQLite for Dev)
* **Caching & Broker:** Redis
* **Async Tasks:** Celery
* **API Testing:** Postman

## ⚙️ Installation & Setup

1.  **Clone the repo**
    ```bash
    git clone [https://github.com/prachanda980/imdb-clone](https://github.com/prachanda980/imdb-clone.git)
    cd imdb-clone-api
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Redis (Required)**
    ```bash
    # Docker
    docker run -d -p 6379:6379 redis
    # OR Local
    redis-server
    ```

5.  **Migrations & Superuser**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  **Run Servers**
    * **Terminal 1 (Django):**
        ```bash
        python manage.py runserver
        ```
    * **Terminal 2 (Celery Worker):**
        ```bash
        # Mac/Linux
        celery -A core worker --loglevel=info
        # Windows
        celery -A core worker --pool=solo --loglevel=info
        ```

## 📡 API Endpoints (Quick Reference)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/auth/register/` | Create new account |
| **POST** | `/api/auth/login/` | Get JWT Tokens (Triggers Async Email) |
| **GET** | `/api/v1/movies/` | List all movies (Redis Cached) |
| **POST** | `/api/v1/movies/` | Add new movie (Admin only) |
| **POST** | `/api/v1/movies/1/reviews/` | Add review to movie ID 1 |
| **POST** | `/api/v1/movies/1/crew/` | Link actor/director to movie |

## 🧪 Testing

To run the automated test suite:
```bash
python manage.py test