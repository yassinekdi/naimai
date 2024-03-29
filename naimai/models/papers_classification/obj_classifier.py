from transformers import AutoModelForSequenceClassification, AutoTokenizer
from naimai.constants.paths import path_objective_classifier
import torch

class Objective_classifier:
    def __init__(self,model=None,tokenizer=None):
        if model and tokenizer:
            self.model= model
            self.tokenizer =  tokenizer
        else:
            self.model = AutoModelForSequenceClassification.from_pretrained(path_objective_classifier, num_labels=2)
            self.tokenizer = AutoTokenizer.from_pretrained(path_objective_classifier)
            if torch.cuda.is_available():
                print('  >> GPU Used in objective classification !')
                self.model = self.model.to('cuda')

    def sentence_is_objective(self,sentence):
        txt_tokenized = self.tokenizer(sentence, truncation=True, padding=True, return_tensors='pt')
        if torch.cuda.is_available():
            txt_tokenized=txt_tokenized.to("cuda")
        outputs = self.model(**txt_tokenized)
        probs = outputs[0].softmax(1)
        idx = probs.argmax()
        prediction = int(idx.cpu().numpy())
        if prediction > 0:
            return True
        return False

    def predict(self,list_objectives):
        result = [sentence for sentence in list_objectives if self.sentence_is_objective(sentence)]
        return result