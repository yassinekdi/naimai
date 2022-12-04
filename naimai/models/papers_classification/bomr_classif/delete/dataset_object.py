import ast
from torch.utils.data import Dataset
import torch

class dataset_base(Dataset):
    def __init__(self, dataframe, tokenizer, max_len):
        self.len = len(dataframe)
        self.data = dataframe
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return self.len


class dataset(dataset_base):
    def __init__(self, dataframe, tokenizer, max_len, get_wids, label_all_tokens):
        super().__init__(dataframe=dataframe, tokenizer=tokenizer, max_len=max_len)
        self.len = len(dataframe)
        self.data = dataframe
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.get_wids = get_wids
        output_labels = ['O', 'B-background', 'I-background', 'B-objectives', 'I-objectives',
                         'B-methods', 'I-methods', 'B-results', 'I-results']
        self.labels2ids = {v: k for k, v in enumerate(output_labels)}
        self.label_all_tokens = label_all_tokens
        # self.ids2labels = {k:v for k,v in enumerate(output_labels)}

    def get_text_and_word_labels(self, index):
        text = self.data.text[index]
        word_labels = ast.literal_eval(self.data.entities[index]) if not self.get_wids else None
        return text, word_labels

    def tokenize(self, text):
        encoding = self.tokenizer(text.split(),
                                  is_split_into_words=True,
                                  padding='max_length',
                                  truncation=True,
                                  max_length=self.max_len)
        return encoding

    def create_labels_ids(self, word_ids, word_labels):
        label_ids = []
        if not self.get_wids:
            previous_word_idx = None
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(self.labels2ids[word_labels[word_idx]])
                else:
                    if self.label_all_tokens:
                        label_ids.append(self.labels2ids[word_labels[word_idx]])
                    else:
                        label_ids.append(-100)
                previous_word_idx = word_idx
        return label_ids

    def encoding2torch_tensor(self, word_ids, encoding):
        item = {key: torch.as_tensor(val) for key, val in encoding.items()}

        if self.get_wids:
            word_ids2 = [w if w is not None else -1 for w in word_ids]
            item['wids'] = torch.as_tensor(word_ids2)
        return item

    def __getitem__(self, index):
        # step 1: get the text and word labels
        text, word_labels = self.get_text_and_word_labels(index)

        # Tokenize text & get words ids
        encoding = self.tokenize(text)
        word_ids = encoding.word_ids()

        # Create labels ids
        encoding['labels'] = self.create_labels_ids(word_ids, word_labels)

        # Convert to torch tensors
        item = self.encoding2torch_tensor(word_ids, encoding)

        return item