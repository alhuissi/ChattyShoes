import pinecone
import os
import openai
from flask import jsonify
import csv
import requests
import re
import time
from io import StringIO
from bs4 import BeautifulSoup
import html
import functions_framework
import logging
logging.basicConfig(level=logging.INFO)

pinecone_api_key = os.environ["PINECONE_API_KEY"]
pinecone_env = os.environ["PINECONE_ENV"]
openai.api_key = os.environ["OPENAI_API_KEY"]
embed_model = "text-embedding-ada-002"
index_name = "test"
pinecone_dimension = 1536
batch_size = 100

def clean_html(text):
    """
    Clean HTML tags, entities, and special characters from a text string.

    :param text: Input HTML text to be cleaned
    :type text: str
    :return: Cleaned text
    :rtype: str
    """
    # Check if text is None or not a string, if so, return an empty string
    if text is None or not isinstance(text, str):
        return ""

    # Remove HTML tags using Beautiful Soup library
    soup = BeautifulSoup(text, "html.parser")
    text_without_html = soup.get_text(separator=" ")

    # Replace HTML entities with their corresponding characters
    text_without_html = html.unescape(text_without_html)

    # Remove any remaining special characters
    cleaned_text = re.sub(r'[^\w\s]', '', text_without_html)

    # Replace newline and carriage return with space
    cleaned_text = re.sub(r'[\n\r\xa0]+', ' ', cleaned_text)
    
    return cleaned_text.strip()  # Return text after stripping leading/trailing whitespace

def extract_data_from_csv(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we got a valid response

    # Decode the response content manually with UTF-8
    text = response.content.decode('utf-8')
    csvfile = StringIO(text)
    reader = csv.DictReader(csvfile)
    data = []
    current_product = None
    for row in reader:
        if row['Title'] and row['Body (HTML)']:  # This is a new product
            if current_product:  # Save the previous product
                data.append(current_product)
            current_product = {
                'id': row['Handle'],
                'title': row['Title'],
                'description': clean_html(row['Body (HTML)']),
                'sizes': [],
                'image': row['Image Src'],
                'vendor': row['Vendor'],
                'category': row['Product Category'],
                'type': row['Type'],
                'tags': row['Tags'].split(', ')
            }
        # Add the size to the current product
        current_product['sizes'].append(row['Option1 Value'])
    # Don't forget to add the last product
    if current_product:
        data.append(current_product)
    return data


@functions_framework.http
def convert_csv_to_bibliotheca(request):
    url = request.json.get('url')
    logging.info("Initing pinecone")
    pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
    #if index_name in pinecone.list_indexes():
    #    logging.info("Deleting index")
        # if exists, delete index
    #    pinecone.delete_index(index_name)   
    # create index
    #logging.info("Create index")
    #pinecone.create_index(
    #    index_name,
    #    dimension=pinecone_dimension,
    #    metric='cosine',
    #    metadata_config={'indexed': ['channel_id', 'published']}
    #)
    # connect to index
    if index_name not in pinecone.list_indexes():
        return 'Index does not exist', 404
    logging.info("Connect to index")
    index = pinecone.GRPCIndex(index_name) 

    # get data
    logging.info("Extracting data")
    data = extract_data_from_csv(url)

    # upsert to Pinecone
    logging.info("Upserting to pinecone")
    for i in range(0, len(data), batch_size):
        # find end of batch
        i_end = min(len(data), i+batch_size)
        meta_batch = data[i:i_end]
        # get ids
        ids_batch = [x['id'] for x in meta_batch]
        # get texts to encode
        texts = [x['description'] for x in meta_batch]
        # create embeddings (try-except added to avoid RateLimitError)
        try:
            res = openai.Embedding.create(input=texts, engine=embed_model)
        except:
            done = False
            while not done:
                time.sleep(5)
                try:
                    print(texts)
                    res = openai.Embedding.create(input=texts, engine=embed_model)
                    done = True
                except Exception as e:
                    print(e)
                    pass
        embeds = [record['embedding'] for record in res['data']]
        # cleanup metadata
        meta_batch = [{
            'title': x['title'],
            'description': x['description'],
            'sizes': x['sizes'],
            'image': x['image'],
            'vendor': x['vendor'],
            'category': x['category'],
            'type': x['type'],
            'tags': x['tags']
            } for x in meta_batch]
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        # upsert to Pinecone
        index.upsert(vectors=to_upsert)

    return 'CSV converted to Bibliotheca successfully', 200

@functions_framework.http
def query_bibliotheca(request):
    # get query
    query = request.json.get('query')
    logging.info("Initing pinecone")
    pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
    if index_name not in pinecone.list_indexes():
        return 'Index does not exist', 404
    # connect to index
    index = pinecone.GRPCIndex(index_name) 
    index.describe_index_stats()

    embed_query = openai.Embedding.create(
        input=[query],
        engine=embed_model
    )

    # retrieve from Pinecone
    xq = embed_query['data'][0]['embedding']

    # get relevant contexts (including the questions)
    res = index.query(xq, top_k=2, include_metadata=True)['matches']

    # get results
    results = []
    response_message ="Query results:"
    for i in range(len(res)):
        results.append({
            'title': res[i].metadata['title'],
            'description': res[i].metadata['description'],
            'sizes': res[i].metadata['sizes'],
            'image': res[i].metadata['image'],
            'vendor': res[i].metadata['vendor'],
            'category': res[i].metadata['category'],
            'type': res[i].metadata['type'],
            'tags': res[i].metadata['tags'],
            'score': res[i].score
        })
        response_message = response_message + """
        - """ + res[i].metadata['title'] + """
            - id: """ + res[i].id + """
            - description: """ + res[i].metadata['description'] + """
            - sizes: """ + str(res[i].metadata['sizes']) + """
            - image: """ + res[i].metadata['image']
        
    final_response = {
        'responseMessage': response_message,
        'results': results
    }

    return jsonify(final_response), 200