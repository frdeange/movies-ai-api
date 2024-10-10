import requests
import json
from flask import Flask, jsonify, request, send_from_directory, Response
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask_swagger_ui import get_swaggerui_blueprint
from collections import OrderedDict

app = Flask(__name__)

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

def get_cinemas_data():
    # Base URL of the web page
    base_url = "https://www.sensacine.com/cines/provincias-27410/"

    # Make the HTTP request to the web page
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Get the total number of pages
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    pagination = soup.find('div', class_='pagination-item-holder')
    if pagination:
        last_page_element = pagination.find_all('a', class_='button')[-1]
        total_pages = int(last_page_element.text.strip())
    else:
        total_pages = 1

    cinemas_data = []

    # Iterate through all pages
    for current_page in range(1, total_pages + 1):
        # Request the current page
        url = f"{base_url}?page={current_page}"
        response = requests.get(url, headers=headers)

        # Parse the page content with Beautiful Soup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all cinema elements
        cinemas = soup.find_all('div', class_='theater-card hred cf card-thumb-large')

        for cinema in cinemas:
            # Extract the cinema name
            name_element = cinema.find('h3', class_='title')
            name = name_element.text.strip() if name_element else "Name not available"

            # Extract the cinema address
            address_element = cinema.find('address', class_='address')
            address = address_element.text.strip() if address_element else "Address not available"

            # Extract the number of screens
            screens_element = cinema.find('div', class_='screen-number')
            screens = screens_element.text.strip() if screens_element else "Number of screens not available"

            # Extract the cinema ID from data-theater attribute
            data_theater_element = cinema.find('span', class_='add-theater-anchor')
            cinema_id = None
            if data_theater_element and data_theater_element.has_attr('data-theater'):
                data_theater = data_theater_element['data-theater']
                cinema_id = eval(data_theater).get('id')  # Convert string to dictionary and get the id

            # Create the cinema URL using the ID
            cinema_url = f"https://www.sensacine.com/cines/cine/{cinema_id}/" if cinema_id else "URL not available"

            # Create a dictionary with the cinema data
            cinema_data = OrderedDict([
                ("name", name),
                ("address", address),
                ("num_screens", screens),
                ("url", cinema_url),
                ("movies", [])
            ])
            print(cinema_data)
            # Get movies for the cinema
            cinema_response = requests.get(cinema_url)
            if cinema_response.status_code == 200:
                cinema_soup = BeautifulSoup(cinema_response.content, 'lxml')

                for i in range(1):
                    date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                    date_url = cinema_url + f"#shwt_date={date}"

                    date_response = requests.get(date_url)

                    if date_response.status_code == 200:
                        date_soup = BeautifulSoup(date_response.content, 'lxml')
                        movies = date_soup.find_all('div', class_='card entity-card entity-card-list movie-card-theater cf hred')

                        if movies:
                            for movie in movies:
                                movie_title = movie.find('a', class_='meta-title-link')
                                # showtimes = movie.find_all('span', class_='showtimes-hour-item-value')
                                
                                if movie_title: # and showtimes:
                                    movie_data = OrderedDict([
                                        ("title", movie_title.text.strip())
                                    ])
                                    # OLD VERSION 
                                    # movie_data = {
                                        #"title": movie_title.text.strip(),
                                        # "showtimes": [showtime.text.strip() for showtime in showtimes],
                                        # "date": date
                                    #}
                                    cinema_data["movies"].append(movie_data)

            cinemas_data.append(cinema_data)

    return cinemas_data

@app.route('/cinemas', methods=['GET'])
def get_cinemas():    
    cinemas_data = get_cinemas_data()
    if cinemas_data is None:
        return jsonify({"error": "Could not retrieve cinema data"}), 500

    # Convertir a JSON garantizando que el orden de los campos se mantenga
    response_json = json.dumps(cinemas_data, ensure_ascii=False, indent=2)

    # Usar Flask Response para devolver el JSON
    return Response(response_json, content_type='application/json')

@app.route('/movies', methods=['GET'])
def get_movies():
    cinemas_data = get_cinemas_data()
    if cinemas_data is None:
        return jsonify({"error": "Could not retrieve cinema data"}), 500
    
    cinemas_summary = []
    for cinema in cinemas_data:
        cinema_summary = {
            "name": cinema["name"],
            "address": cinema["address"],
            "num_screens": cinema["num_screens"],
            "url": cinema["url"],
            "movies": [
                {"title": movie["title"]} for movie in cinema["movies"]
            ]
        }
        cinemas_summary.append(cinema_summary)
    
    return jsonify(cinemas_summary)

@app.route('/showtimes', methods=['GET'])
def get_showtimes():
    cinema_name = request.args.get('cinema')
    movie_title = request.args.get('movie')
    
    if not cinema_name or not movie_title:
        return jsonify({"error": "Parameters 'cinema' and 'movie' are required"}), 400
    
    cinemas_data = get_cinemas_data()
    if cinemas_data is None:
        return jsonify({"error": "HTTP request error or no cinemas found"}), 500
    
    for cinema in cinemas_data:
        if cinema["name"].lower() == cinema_name.lower():

            for movie in cinema["movies"]:
                if movie["title"].lower() == movie_title.lower():
                    return jsonify({
                        "cinema": cinema["name"],
                        "address": cinema["address"],
                        "title": movie["title"],
                        
                    })
    
    return jsonify({"error": "No showtimes found for the specified movie in the cinema"}), 404

@app.route('/cinema_showtimes', methods=['GET'])
def get_cinema_showtimes():
    cinema_name = request.args.get('cinema')

    if not cinema_name:
        return jsonify({"error": "Parameter 'cinema' is required"}), 400
    
    cinemas_data = get_cinemas_data()
    if cinemas_data is None:
        return jsonify({"error": "HTTP request error or no cinemas found"}), 500
    
    for cinema in cinemas_data:
        if cinema["name"].lower() == cinema_name.lower():
            return jsonify(cinema["movies"])
    
    return jsonify({"error": "No showtimes found for the specified cinema"}), 404

@app.route('/cinemas_movie', methods=['GET'])
def get_cinemas_movie():
    movie_title = request.args.get('movie')
    
    if not movie_title:
        return jsonify({"error": "Parameter 'movie' is required"}), 400
    
    cinemas_data = get_cinemas_data()
    if cinemas_data is None:
        return jsonify({"error": "HTTP request error or no cinemas found"}), 500
    
    cinemas_movie = []
    for cinema in cinemas_data:
        for movie in cinema["movies"]:
            if movie["title"].lower() == movie_title.lower():
                cinemas_movie.append({
                    "cinema": cinema["name"],
                    "address": cinema["address"],
                    "showtimes": movie["showtimes"],
                    "date": movie["date"]
                })
    
    if not cinemas_movie:
        return jsonify({"error": "No cinemas found showing the specified movie"}), 404
    
    return jsonify(cinemas_movie)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)