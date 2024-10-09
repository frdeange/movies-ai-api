from flask import Flask, jsonify, request, send_from_directory
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "API de Cines y Películas"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def get_cine_data():
    """
    Fetches cinema data from the Sensacine website for a specific city.
    This function scrapes the Sensacine website to retrieve information about cinemas in a specific city,
    including their names, addresses, URLs, and the movies they are showing over the next 7 days.
    Returns:
        list: A list of dictionaries, each containing the following keys:
            - "nombre" (str): The name of the cinema.
            - "direccion" (str): The address of the cinema.
            - "url" (str): The URL to the cinema's page on Sensacine.
            - "peliculas" (list): A list of dictionaries, each containing:
                - "titulo" (str): The title of the movie.
                - "horarios" (list): A list of showtimes for the movie.
                - "fecha" (str): The date for which the showtimes are listed.
        None: If the request to the Sensacine website fails or no cinemas are found.
    """
    url = "https://www.sensacine.com/cines/ciudades-72368/"

    # Gets the HTML content of the page
    response = requests.get(url)
    
    # Checks if the request was successful
    if response.status_code != 200:
        return None
    
    # Parses the HTML content
    soup = BeautifulSoup(response.content, 'lxml')

    # Finds all the div elements with the class 'meta meta-theater'
    cines = soup.find_all('div', class_='meta meta-theater')
    
    # Checks if any cines were found
    if not cines:
        return None
    
    cines_data = []
    
    # Iterates over the cines
    for cine in cines:
        # Finds the h2 element with the class 'title'
        nombre_cine = cine.find('h2', class_='title')
        # Finds the address element with the class 'address address-without-acces'
        direccion_cine = cine.find('address', class_='address address-without-acces')
        # Finds the a element with the href attribute
        enlace_cine = cine.find('a', href=True)
        # num salas
        num_salas = cine.find(class_='screen-number')

        # Checks if all the required elements were found
        if nombre_cine and direccion_cine and enlace_cine:
            # Creates a dictionary with the data
            cine_data = {
                "nombre": nombre_cine.text.strip(),
                "direccion": direccion_cine.text.strip(),
                "url": "https://www.sensacine.com" + enlace_cine['href'],
                "num_salas": num_salas.text.strip()
            }
            
            # # Fetches the URL of the cinema
            # cine_url = cine_data["url"]

            # cine_response = requests.get(cine_url)
            
            # if cine_response.status_code == 200:
            #     cine_soup = BeautifulSoup(cine_response.content, 'lxml')
                
            #     for i in range(7):
            #         date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            #         date_url = cine_url + f"#shwt_date={date}"
                    
            #         date_response = requests.get(date_url)
                    
            #         if date_response.status_code == 200:
            #             date_soup = BeautifulSoup(date_response.content, 'lxml')
            #             peliculas = date_soup.find_all('div', class_='card entity-card entity-card-list movie-card-theater cf hred')
                        
            #             if peliculas:
            #                 for pelicula in peliculas:
            #                     titulo_pelicula = pelicula.find('a', class_='meta-title-link')
            #                     horarios = pelicula.find_all('span', class_='showtimes-hour-item-value')
                                
            #                     if titulo_pelicula and horarios:
            #                         pelicula_data = {
            #                             "titulo": titulo_pelicula.text.strip(),
            #                             "horarios": [horario.text.strip() for horario in horarios],
            #                             "fecha": date
            #                         }
            #                         cine_data["peliculas"].append(pelicula_data)
            cines_data.append(cine_data)
    
    return cines_data

@app.route('/cines', methods=['GET'])
def get_cines():
    cines_data = get_cine_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    return jsonify(cines_data)

@app.route('/peliculas', methods=['GET'])
def get_peliculas():
    cines_data = get_cine_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    peliculas_data = []
    for cine in cines_data:
        for pelicula in cine["peliculas"]:
            peliculas_data.append({
                "cine": cine["nombre"],
                "direccion": cine["direccion"],
                "titulo": pelicula["titulo"],
                "horarios": pelicula["horarios"],
                "fecha": pelicula["fecha"]
            })
    
    return jsonify(peliculas_data)

@app.route('/horarios', methods=['GET'])
def get_horarios():
    cine_nombre = request.args.get('cine')
    pelicula_titulo = request.args.get('pelicula')
    
    if not cine_nombre or not pelicula_titulo:
        return jsonify({"error": "Parámetros 'cine' y 'pelicula' son requeridos"}), 400
    
    cines_data = get_cine_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    for cine in cines_data:
        if cine["nombre"].lower() == cine_nombre.lower():
            for pelicula in cine["peliculas"]:
                if pelicula["titulo"].lower() == pelicula_titulo.lower():
                    return jsonify({
                        "cine": cine["nombre"],
                        "direccion": cine["direccion"],
                        "titulo": pelicula["titulo"],
                        "horarios": pelicula["horarios"],
                        "fecha": pelicula["fecha"]
                    })
    
    return jsonify({"error": "No se encontraron horarios para la película en el cine especificado"}), 404

@app.route('/cines_pelicula', methods=['GET'])
def get_cines_pelicula():
    pelicula_titulo = request.args.get('pelicula')
    
    if not pelicula_titulo:
        return jsonify({"error": "Parámetro 'pelicula' es requerido"}), 400
    
    cines_data = get_cine_data()
    if cines_data is None:
        return jsonify({"error": "Error en la solicitud HTTP o no se encontraron cines"}), 500
    
    cines_pelicula = []
    for cine in cines_data:
        for pelicula in cine["peliculas"]:
            if pelicula["titulo"].lower() == pelicula_titulo.lower():
                cines_pelicula.append({
                    "cine": cine["nombre"],
                    "direccion": cine["direccion"],
                    "horarios": pelicula["horarios"],
                    "fecha": pelicula["fecha"]
                })
    
    if not cines_pelicula:
        return jsonify({"error": "No se encontraron cines que emitan la película especificada"}), 404
    
    return jsonify(cines_pelicula)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)