import pickle
from gibberish_detector import gib_detect_train

model_data = pickle.load(open('../pdfparser-pipeline/gibberish_detector/gib_model.pki', 'rb'))


def predictGibberish(string: str) -> bool:
    model_mat = model_data['mat']
    threshold = model_data['thresh']
    return gib_detect_train.avg_transition_prob(string, model_mat) > threshold
