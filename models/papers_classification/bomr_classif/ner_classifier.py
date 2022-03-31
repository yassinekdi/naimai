# from transformers import AutoModelForTokenClassification, AutoTokenizer, TrainingArguments, \
#      DataCollatorForTokenClassification
from transformers import TrainingArguments, DataCollatorForTokenClassification
from datasets import Dataset, load_metric
from naimai.utils.general import correct_ner_data
from naimai.utils.transformers import visualize
from naimai.constants.models import output_labels
from naimai.constants.paths import path_ner_data_total
from .trainer import BOMR_Trainer, Predictions_preparer
import pandas as pd
import numpy as np
import torch

metric = load_metric("seqeval")

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (special tokens)
    true_predictions = [
        [output_labels[eval_pred] for (eval_pred, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [output_labels[l] for (eval_pred, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "accuracy": results["overall_accuracy"],
    }

class NER_BOMR_classifier:
    def __init__(self, config, path_ner_data=path_ner_data_total, ner_data_df=None, model=None, tokenizer=None,label_all_subtokens=False,load_model=False,path_model=None):
        self.config = config
        self.tokenized_data = None
        self.trainer = None
        self.datasets = None
        self.label_all_subtokens = label_all_subtokens

        # LABELS ----------------

        self.ids2labels = {k: v for k, v in enumerate(output_labels)}
        self.labels2ids = {v: k for k, v in enumerate(output_labels)}

        # DATA -----------------
        if isinstance(ner_data_df, pd.DataFrame):
            self.NER_data_df = ner_data_df
        else:
            df = pd.read_csv(path_ner_data)
            df['entities'] = df.apply(correct_ner_data, axis=1)
            df['tokens'] = df['text'].str.split()
            df['ner_tags'] = df['entities'].apply(lambda x: [self.labels2ids[elt] for elt in x])
            self.NER_data_df = df.dropna()
            print(f'NER data shape : {self.NER_data_df.shape}')

        # TOKENIZER ------------------
        if tokenizer:
            self.tokenizer = tokenizer
        elif load_model:
            self.load_model(path_model)
        else:
            print('Getting Tokenizer..')
            # self.tokenizer = AutoTokenizer.from_pretrained(config['tokenizer_name'])

        # MODEL  ----------------
        if model:
            self.model = model
        elif load_model:
            pass
        else:
            print('Model creation..')
            # self.model = AutoModelForTokenClassification.from_pretrained(config['model_name'],
            #                                                              num_labels=len(output_labels))

        # Data Collator ------------
        self.data_collator = DataCollatorForTokenClassification(self.tokenizer)

        # Training ARGS ----------
        self.training_args = TrainingArguments(
            output_dir=f"{self.config['output_dir']}",
            save_total_limit = 1,
            evaluation_strategy="epoch",
            logging_strategy="epoch",
            save_strategy="epoch",
            learning_rate=config['learning_rates'],
            per_device_train_batch_size=config['batch_size'],
            per_device_eval_batch_size=config['batch_size'],
            num_train_epochs=config['epochs'],
            weight_decay=config['weight_decay'],
        )

    def tokenize_and_align_labels(self, examples):
        tokenized_inputs = self.tokenizer(examples["tokens"], truncation=True, is_split_into_words=True,
                                          padding='max_length',max_length=self.config['max_length'])

        labels = []
        for i, label in enumerate(examples[f"ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)  # Map tokens to their respective word.
            previous_word_idx = None
            label_ids = []
            for word_idx in word_ids:  # Set the special tokens to -100.
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:  # Only label the first token of a given word.
                    try:
                        label_ids.append(label[word_idx])
                    except:
                        print(f'idx {i}, widx = {word_idx}, label {label}, len word ids= {len(word_ids)}')
                        label_ids.append(-100)
                else:
                    if self.label_all_subtokens:
                        label_ids.append(label[word_idx])
                    else:
                        label_ids.append(-100)
                previous_word_idx = word_idx
            labels.append(label_ids)


        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    def get_train_validation_data(self, test_size=.20, seed=42):
        ds = Dataset.from_pandas(self.NER_data_df[['doi', 'tokens', 'ner_tags']])
        self.datasets = ds.train_test_split(test_size=test_size, shuffle=True, seed=seed)

    def tokenize_data(self):
        self.tokenized_data = self.datasets.map(self.tokenize_and_align_labels, batched=True)

    def get_trainer(self):
        self.trainer = BOMR_Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.tokenized_data["train"],
            eval_dataset=self.tokenized_data["test"],
            data_collator=self.data_collator,
            tokenizer=self.tokenizer,
            compute_metrics=compute_metrics
        )

    def train(self):
        self.trainer.train()

    def load_model(self,path_model):
        print('Loading model & tokenizer...')
        self.model = AutoModelForTokenClassification.from_pretrained(path_model, num_labels=len(output_labels))
        self.tokenizer = AutoTokenizer.from_pretrained(path_model)
        if torch.cuda.is_available():
            print('  >> GPU Used in objective classification !')
            self.model = self.model.to('cuda')

    def predict(self,text,visualize_=True):
        tokens = text.split()
        if torch.cuda.is_available():
            encoding = self.tokenizer(tokens, truncation=True, is_split_into_words=True,return_tensors='pt',padding='max_length',max_length=self.config['max_length']).to('cuda')
        else:
            encoding = self.tokenizer(tokens, truncation=True, is_split_into_words=True, return_tensors='pt')
        outputs = self.model(**encoding)
        prediction = outputs.logits.argmax(-1)[0]

        prp = Predictions_preparer(predictions=prediction,
                                   tokenizer=self.tokenizer,
                                   datasets=None)
        df = prp.prepare_one_prediction("doi", prediction, tokens)
        if visualize_:
            visualize(text,df)
        return df
