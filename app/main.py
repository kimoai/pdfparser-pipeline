from PyPDF2 import PdfReader
import re
import requests
import pymongo
import settings
from tqdm import tqdm
from pymongo import UpdateOne
import io
import tesserocr
from pdf2image import convert_from_bytes
import logging
import time
from app.gibberish_detector.gib_detect import predictGibberish

client = pymongo.mongo_client.MongoClient(settings.MONGO_URI)
db = client['content']
collection = db['content']

api = tesserocr.PyTessBaseAPI()

logger = logging.getLogger(__name__)
handler = logging.FileHandler('log_file.log')
logging.getLogger().setLevel(logging.INFO)


def flush_queue(queue):
    logging.info('Flushing parse queue!')
    print('Flushing parse queue!')
    if len(queue) > 0:
        collection.bulk_write(queue, ordered=False)
    return []


def processText(text: str) -> str:
    text = text.replace("\n", ' ')
    text = re.sub(r'\d', '', text)
    text = re.sub(r'\x7f', '', text)
    text = re.sub(r'\t', '', text)
    text = re.sub('[\s.]+\w+$', '. ', text)
    text = re.sub(' +', ' ', text)

    return text


def parsePDF(bites: bytes) -> str:
    with io.BytesIO() as stream:
        try:
            stream.write(bites)
            stream.seek(0)
            reader = PdfReader(stream)

            failed = 0
            text_tot = []
            for page in reader.pages:
                text = page.extract_text()
                if len(text) > 0:
                    # found gibberish, trust is broken, exit function
                    return '<FAILED>'
                else:
                    if predictGibberish(text) == False:
                        text = processText(text)
                        text_tot.append(text)
                    else:
                        failed += 1
                        # wait 4 pages before saying it does not work
                        if failed == 5:
                            # parsing does not work move to OCR
                            return '<FAILED>'
            return '. '.join(text_tot)
        except:
            return '<FAILED>'


def parseWithOCR(bites: bytes) -> str:
    try:
        pdf_pages = convert_from_bytes(bites, use_pdftocairo=True, grayscale=True, thread_count=2, timeout=60, size=(1200, 2000),
                                       last_page=settings.MAX_PAGES)
        text_tot = []

        # compute max 5 pages
        for page_enumeration, pil_image in enumerate(pdf_pages, start=1):
            api.SetImage(pil_image)
            text = api.GetUTF8Text()
            text = processText(text)
            text_tot.append(text)

        if len(text_tot) > 0:
            parsed_text = '. '.join(text_tot)
            return parsed_text
        else:
            return '<FAILED>'
    except:
        return '<FAILED>'


def parsePDFcontent():
    logging.info('STARTED PARSING')
    filter = {'content_type': {'$in': ['cheatsheets', 'slides', 'reports']},
              'text': {'$eq': None}}
    projection = {'content_url': 1, '_id': 1, 'url': 1, 'content_type': 1}

    docs = collection.find(filter, projection)

    queue = []
    start = time.time()
    for i, doc in enumerate(tqdm(docs)):
        content_url = doc.get('content_url')
        if not content_url:
            content_url = doc.get('url')

        logging.info(f'element num {i}, id: {doc}')
        if not content_url:
            logging.info(f'parsing failed for id {doc["_id"]}, missing content_url')
            continue
        # check if is pdf
        elif not content_url.endswith('.pdf'):
            logging.info(f'parsing failed for id {doc["_id"]}, url is not pdf')
            continue
        else:
            response = requests.get(content_url)
            # check if download is succesful
            if response.status_code != 200:
                logging.info(f'parsing failed for id {doc["_id"]}, download failed')
                continue
            else:
                parsed_text = parsePDF(response.content)
                if parsed_text == '<FAILED>':
                    # try OCR
                    parsed_text = parseWithOCR(response.content)
                    if parsed_text == '<FAILED>':
                        logging.info(f'parsing failed for id {doc["_id"]}, parsing failed')
                        continue

                # everything went well upload to mongo
                _id = doc['_id']

                #one last check to be sure we upload meaningful text
                if predictGibberish(parsed_text) == True:
                    update = UpdateOne({'_id': _id}, {'$set': {'text': parsed_text, 'run_vectorizer': True}},
                                       upsert=False)
                    queue.append(update)

                if len(queue) >= settings.MONGO_BATCH_SIZE:
                    queue = flush_queue(queue)
                    logging.info(f"added 10 new texts in {time.time() - start}")
                    start = time.time()

    queue = flush_queue(queue)
    return 'DONE'


if __name__ == "__main__":
    parsePDFcontent()
