# Cinema and Movies API

This API allows you to query information about cinemas and movies in Madrid. It provides endpoints to get a list of cinemas, movies, showtimes, and more.

## Table of Contents

- [Getting Started](#getting-started)
- [Endpoints](#endpoints)
- [Running the Application](#running-the-application)
- [Swagger Documentation](#swagger-documentation)

## Getting Started

### Prerequisites

- Docker
- Python 3.x
- pip

### Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Build and run the Docker container:
    ```sh
    docker-compose up --build
    ```

3. Alternatively, you can set up the environment manually:
    ```sh
    pip install -r requirements.txt
    python3 app.py
    ```

## Endpoints

### Get List of Cinemas

- **URL:** `/cines`
- **Method:** `GET`
- **Response:**
    ```json
    [
        {
            "nombre": "Cines Callao",
            "direccion": "Plaza Callao 3 28013 Madrid",
            "url": "https://www.sensacine.com/cines/cine/E0146/",
            "peliculas": [
                {
                    "titulo": "La virgen roja",
                    "horarios": ["16:00"],
                    "fecha": "2023-10-01"
                }
            ]
        }
    ]
    ```

### Get List of Movies

- **URL:** `/peliculas`
- **Method:** `GET`
- **Response:**
    ```json
    [
        {
            "titulo": "La virgen roja",
            "horarios": ["16:00"],
            "fecha": "2023-10-01"
        }
    ]
    ```

### Get Showtimes for a Movie in a Cinema

- **URL:** `/horarios`
- **Method:** `GET`
- **Query Parameters:**
    - `cine`: Name of the cinema (required)
    - `pelicula`: Title of the movie (required)
- **Response:**
    ```json
    {
        "cine": "Cines Callao",
        "direccion": "Plaza Callao 3 28013 Madrid",
        "titulo": "La virgen roja",
        "horarios": ["16:00"],
        "fecha": "2023-10-01"
    }
    ```

### Get Cinemas Showing a Specific Movie

- **URL:** `/cines_pelicula`
- **Method:** `GET`
- **Query Parameters:**
    - `pelicula`: Title of the movie (required)
- **Response:**
    ```json
    [
        {
            "cine": "Cines Callao",
            "direccion": "Plaza Callao 3 28013 Madrid",
            "horarios": ["16:00"],
            "fecha": "2023-10-01"
        }
    ]
    ```

## Running the Application

To run the application, use the following command:

```sh
python3 [app.py](http://_vscodecontentref_/#%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22path%22%3A%22%2Fworkspaces%2Fmoviesassistant%2Fapp.py%22%2C%22scheme%22%3A%22vscode-remote%22%2C%22authority%22%3A%22dev-container%2B7b22686f737450617468223a22633a5c5c7265706f735c5c6d6f76696573617373697374616e74222c226c6f63616c446f636b6572223a66616c73652c22636f6e66696746696c65223a7b22246d6964223a312c2270617468223a222f433a2f7265706f732f6d6f76696573617373697374616e742f2e646576636f6e7461696e65722f646576636f6e7461696e65722e6a736f6e222c22736368656d65223a2266696c65227d7d%22%7D%7D)