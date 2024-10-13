import json
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from datetime import datetime
from azure.cosmos import CosmosClient, exceptions
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get the environment variables for Azure Cosmos DB
AZURE_COSMOSDB_URI = os.getenv("AZURE_COSMOSDB_URI")
AZURE_COSMOSDB_KEY = os.getenv("AZURE_COSMOSDB_KEY")
AZURE_COSMOSDB_DATABASE_NAME = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
AZURE_COSMOSDB_CONTAINER_NAME = os.getenv("AZURE_COSMOSDB_CONTAINER_NAME")

# Initialize Cosmos DB client
client = CosmosClient(AZURE_COSMOSDB_URI, credential=AZURE_COSMOSDB_KEY)
database = client.get_database_client(AZURE_COSMOSDB_DATABASE_NAME)
container = database.get_container_client(AZURE_COSMOSDB_CONTAINER_NAME)

app = Flask(__name__)
CORS(app)

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Cinema and Movies API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def load_json_data():
    # Get the current date in the format YYYYMMDD
    current_date = datetime.now().strftime('%Y%m%d')
    
    try:
        # Query CosmosDB for the document with the current date
        document = container.read_item(item=current_date, partition_key=current_date)
        return document.get("data")
    except exceptions.CosmosResourceNotFoundError:
        return None

@app.route('/cinemas', methods=['GET'])
def get_cinemas():    
    data = load_json_data()
    if data is None:
        return jsonify({"error": "No cinema data available for today"}), 404

    cinemas_summary = []
    for cinema in data:
        cinema_summary = {
            "id": cinema["id"],
            "name": cinema["name"],
            "address": cinema["address"],
            "num_screens": cinema["num_screens"],
            "url": cinema["url"]
        }
        cinemas_summary.append(cinema_summary)
    
    return jsonify(cinemas_summary)

@app.route('/movies', methods=['GET'])
def get_movies():
    cinema_id = request.args.get('cinema_id')
    
    data = load_json_data()
    if data is None:
        return jsonify({"error": "No cinema data available for today"}), 404
    
    for cinema in data:
        if cinema["id"] == cinema_id:
            return jsonify(cinema["movies"])
    
    return jsonify({"error": "Cinema not found"}), 404

@app.route('/showtimes', methods=['GET'])
def get_showtimes():
    cinema_id = request.args.get('cinema_id')
    movie_title = request.args.get('movie_title')
    
    data = load_json_data()
    if data is None:
        return jsonify({"error": "No cinema data available for today"}), 404
    
    for cinema in data:
        if cinema["id"] == cinema_id:
            for movie in cinema["movies"]:
                if movie["title"].lower() == movie_title.lower():
                    return jsonify({
                        "cinema": cinema["name"],
                        "movie": movie["title"],
                        "showtimes": movie["showtimes"]
                    })
    
    return jsonify({"error": "Showtimes not found for the specified movie in the cinema"}), 404

@app.route('/cinemas_movie', methods=['GET'])
def get_cinemas_movie():
    movie_title = request.args.get('movie_title')
    
    data = load_json_data()
    if data is None:
        return jsonify({"error": "No cinema data available for today"}), 404
    
    cinemas_movie = []
    for cinema in data:
        for movie in cinema["movies"]:
            if movie["title"].lower() == movie_title.lower():
                cinemas_movie.append({
                    "cinema": cinema["name"],
                    "address": cinema["address"],
                    "showtimes": movie["showtimes"]
                })
    
    if not cinemas_movie:
        return jsonify({"error": "No cinemas found showing the specified movie"}), 404
    
    return jsonify(cinemas_movie)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)