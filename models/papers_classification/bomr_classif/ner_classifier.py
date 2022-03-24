from transformers import AutoModelForTokenClassification, AutoTokenizer, TrainingArguments, Trainer, \
    DataCollatorForTokenClassification
from datasets import Dataset
from naimai.utils.general import correct_ner_data
import pandas as pd


class NER_BOMR_classifier:
    def __init__(self, config, path_ner_data=None, ner_data_df=None, model=None, tokenizer=None):
        self.config = config
        self.tokenized_data = None
        self.trainer = None
        self.datasets = None

        # LABELS ----------------
        output_labels = ['O', 'B-background', 'I-background', 'B-objectives', 'I-objectives',
                         'B-methods', 'I-methods', 'B-results', 'I-results']
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
        else:
            print('Getting Tokenizer..')
            self.tokenizer = AutoTokenizer.from_pretrained(config['model_name'])

        # MODEL  ----------------
        if model:
            self.model = model
        else:
            print('Model creation..')
            self.model = AutoModelForTokenClassification.from_pretrained(config['model_name'],
                                                                         num_labels=len(output_labels))

        # Data Collator ------------
        self.data_collator = DataCollatorForTokenClassification(self.tokenizer)

        # Training ARGS ----------
        self.training_args = TrainingArguments(
            output_dir=f"{config['model_name'][:10]}",
            #  output_dir=f"{config['model_name'][:10]}_batch_{config['batch_size']}_epochs_{config['epochs']}_lr_{config['learning_rates']}",
            evaluation_strategy="epoch",
            learning_rate=config['learning_rates'],
            per_device_train_batch_size=config['batch_size'],
            per_device_eval_batch_size=config['batch_size'],
            num_train_epochs=config['epochs'],
            weight_decay=config['weight_decay'],
        )

    def tokenize_and_align_labels(self, examples):
        tokenized_inputs = self.tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)

        labels = []
        for i, label in enumerate(examples[f"ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)  # Map tokens to their respective word.
            previous_word_idx = None
            label_ids = []
            for word_idx in word_ids:  # Set the special tokens to -100.
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:  # Only label the first token of a given word.
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
        self.trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=self.tokenized_data["train"],
            eval_dataset=self.tokenized_data["test"],
            data_collator=self.data_collator,
            tokenizer=self.tokenizer,
        )

    def train(self):
        self.trainer.train()
