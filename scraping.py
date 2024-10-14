import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import OrderedDict
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the environment variables for Azure Cosmos DB
AZURE_COSMOSDB_URI = os.getenv("AZURE_COSMOSDB_URI")
AZURE_COSMOSDB_KEY = os.getenv("AZURE_COSMOSDB_KEY")
AZURE_COSMOSDB_DATABASE_NAME = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
AZURE_COSMOSDB_CONTAINER_NAME = os.getenv("AZURE_COSMOSDB_CONTAINER_NAME")
AZURE_COSMOSDB_PARTITION_KEY = os.getenv("AZURE_COSMOSDB_PARTITION_KEY")

# Get the environment variables for web scraping
WEB_SCRAPING_URL = os.getenv("WEB_SCRAPING_URL")

# Initialize Cosmos DB client
client = CosmosClient(AZURE_COSMOSDB_URI, {'masterKey': AZURE_COSMOSDB_KEY})
database = client.create_database_if_not_exists(id=AZURE_COSMOSDB_DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=AZURE_COSMOSDB_CONTAINER_NAME,
    partition_key=PartitionKey(path=AZURE_COSMOSDB_PARTITION_KEY),
    offer_throughput=400
)
def scrape_cinemas_data():
    # Base URL of the web page
    base_url = WEB_SCRAPING_URL

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
                ("id", cinema_id),
                ("name", name),
                ("address", address),
                ("num_screens", screens),
                ("url", cinema_url),
                ("movies", [])
            ])

            # Get movies for the cinema for the next 7 days
            if cinema_url != "URL not available":
                for i in range(7):
                    date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                    date_url = cinema_url + f"#shwt_date={date}"
                    # print(f"Fetching movies for cinema: {cinema_data['name']}, URL: {date_url}, Date: {date}")
                    date_response = requests.get(date_url,timeout=(3.05, 27))
                    if date_response.status_code == 200:
                        #time.sleep(1)  # Sleep for 1 second to avoid being blocked
                        date_soup = BeautifulSoup(date_response.content, 'lxml')
                                            
                        movies = date_soup.find_all('div', class_='card entity-card entity-card-list movie-card-theater cf hred')
                        # print(f"Found {len(movies)} movies for cinema: {cinema_data['name']} on date: {date}")
                        if movies:
                            for movie in movies:

                                # Extract the movie ID
                                movie_title_element = movie.find('a', class_='meta-title-link')
                                movie_id = movie_title_element['href'].split('-')[-1][:-1] if movie_title_element else None  # ID sacado de la URL

                                # Extract the title
                                title = movie_title_element.text.strip() if movie_title_element else "Título no disponible"

                                # Extract the director
                                director_element = movie.find('div', class_='meta-body-item meta-body-direction')
                                director = director_element.find('span', class_='dark-grey-link').text.strip() if director_element else "Director no disponible"

                                # Extract the cast
                                cast_element = movie.find('div', class_='meta-body-item meta-body-actor')
                                cast = [actor.text.strip() for actor in cast_element.find_all('span', class_='dark-grey-link')] if cast_element else []

                                # Extract the synopsis
                                synopsis_element = movie.find('div', class_='synopsis')
                                synopsis = synopsis_element.find('div', class_='content-txt').text.strip() if synopsis_element else "Sinopsis no disponible"
                                
                                # Extract Showtimes and organize by date
                                showtimes_element = movie.find('div', class_='showtimes-anchor')
                                showtimes_by_date = {}
                                if showtimes_element:
                                    showtime_blocks = showtimes_element.find_all('div', class_='showtimes-hour-block')
                                    showtimes = []
                                    for block in showtime_blocks:
                                        time_element = block.find('span', class_='showtimes-hour-item-value')
                                        if time_element:
                                            showtimes.append(time_element.text.strip())
                                    if showtimes:
                                        showtimes_by_date[date] = showtimes

                                # Create Dictionary with movie data
                                movie_data = {
                                    "id": movie_id,
                                    "title": title,
                                    "director": director,
                                    "cast": cast,
                                    "synopsis": synopsis,
                                    "showtimes": showtimes_by_date,
                                }
                                # print(movie_data)

                                cinema_data["movies"].append(movie_data)
                        else:
                            #print("Salta mensaje de alerta")
                            continue
                # Add the cinema data to the list of all cinemas
                cinemas_data.append(cinema_data)

    return cinemas_data

def save_to_json(data):
    # Get the current date in the format YYYYMMDD
    current_date = datetime.now().strftime('%Y%m%d')
    
    # Define the filename with the current date
    filename = f"{current_date}.json"
    
    # Save the data to a JSON file
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)

    print(f"Data saved to {filename}")
    return filename

def check_if_document_exists(document_id):
    query = f"SELECT * FROM c WHERE c.id = '{document_id}'"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    if items:
        return True
    else:
        return False

def save_to_cosmosdb(data):
    # Get the current date in the format YYYYMMDD
    current_date = datetime.now().strftime('%Y%m%d')
    
    # Prepare the document to be stored in CosmosDB
    document = {
        "id": current_date,
        "date": current_date,
        "data": data
    }
    
    # Upsert the document into the CosmosDB container
    container.upsert_item(document)
    print(f"Data saved to Azure CosmosDB with ID: {current_date}")

def scrape_and_save():
    # Get the current date in the format YYYYMMDD
    current_date = datetime.now().strftime('%Y%m%d')
    
    # Check if the document already exists in CosmosDB
    if check_if_document_exists(current_date):
        print(f"Document with ID {current_date} already exists in CosmosDB. Skipping scraping.")
        return
    
    # Scrape the data
    data = scrape_cinemas_data()
    
    # Save the data to a JSON file
    # filename = save_to_json(data)
    
    # Save the data to Azure CosmosDB
    save_to_cosmosdb(data)
    
    return

# If needed, you can call scrape_and_save() here or import this module in your main application.
if __name__ == "__main__":
    scrape_and_save()
