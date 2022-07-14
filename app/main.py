from PyPDF2 import PdfReader
import re
import requests
import pymongo
import settings
from tqdm import tqdm
from pymongo import UpdateOne
import logging

client = pymongo.mongo_client.MongoClient(settings.MONGO_URI)
db = client['content_dev']
collection = db['content']


def flush_queue(queue):
    logging.info('Flushing parse queue!')
    print('Flushing parse queue!')
    if len(queue) > 0:
        collection.bulk_write(queue, ordered=False)
    return []


def parsePDFcontent():
    # filter = {'run_parser': True}
    # projection = {'raw_html': 1, '_id': 1, 'url': 1}
    #
    # docs = collection.find(filter, projection)
    # !/usr/bin/env python

    docs = ["https://storage.googleapis.com/cheatsheets/iot/iot_cheatography_2.pdf"]


    queue = []
    for i, doc in enumerate(tqdm(docs)):
        tempfilename = "temp.pdf"

        response = requests.get(doc)
        file = open(tempfilename, "wb")
        file.write(response.content)
        file.close()

        reader = PdfReader(tempfilename)

        text_tot = []
        for page in reader.pages:
            text = page.extract_text().replace("\n", ' ')
            text = re.sub(r'\d', '', text)
            text_tot.append(text)

        parsed_text = '. '.join(text_tot)

        _id = doc['_id']


        # update = UpdateOne({'_id': _id}, {'$set': {'text': parsed_text, 'run_vectorizer': True}}, upsert=False)
        # queue.append(update)
        #
        # if len(queue) >= settings.MONGO_BATCH_SIZE:
        #     queue = flush_queue(queue)

    # queue = flush_queue(queue)


if __name__ == "__main__":
    parsePDFcontent()