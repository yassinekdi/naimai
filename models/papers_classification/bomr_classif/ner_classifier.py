import numpy as np
import pandas as pd, gc
from sklearn.model_selection import train_test_split
from naimai.utils.transformers import flatten_labels_and_predictions,get_ids_mask_labels, score_feedback_comp
from .dataset_object import dataset
from tqdm.notebook import tqdm
from transformers import AutoTokenizer, AutoModelForTokenClassification
from torch.utils.data import DataLoader
import torch
from sklearn.metrics import accuracy_score


class NER_BOMR_classifier:
    def __init__(self, path_detailed_data, path_ner_data, config, model=None, tokenizer=None):
        self.detailed_data_df = pd.read_csv(path_detailed_data).dropna()  # Df with ['doi', 'text', 'start', 'end', 'predictionstring', 'class', 'class_num', 'len']
        self.NER_data_df = pd.read_csv(path_ner_data).dropna()  # Df with ['doi', 'text', 'entities']
        print('Detailed_data shape : {} -- NER data shape : {}'.format(self.detailed_data_df.shape,
                                                                       self.NER_data_df.shape))
        print(' ')

        self.training_data_df = None  # train_dataset
        self.validation_data_df = None  # validation_dataset
        self.config = config
        self.training_loader = None
        self.validating_loader = None
        if tokenizer:
            self.tokenizer = tokenizer
        else:
            print('Getting Tokenizer..')
            self.tokenizer = AutoTokenizer.from_pretrained(config['model_name'])
            print(' ')

        self.train_params = {'batch_size': config['train_batch_size'],
                             'shuffle': True,
                             'num_workers': 2,
                             'pin_memory': True
                             }
        self.valid_params = {'batch_size': config['valid_batch_size'],
                             'shuffle': False,
                             'num_workers': 2,
                             'pin_memory': True
                             }

        output_labels = ['O', 'B-background', 'I-background', 'B-objectives', 'I-objectives',
                         'B-methods', 'I-methods', 'B-results', 'I-results']
        self.ids2labels = {k: v for k, v in enumerate(output_labels)}
        if model:
            self.model = model
        else:
            print('Model creation..')
            self.model = AutoModelForTokenClassification.from_pretrained(config['model_name'],
                                                                         num_labels=len(output_labels))
            self.model.to(config['device'])
            print(' ')

        print('Optimizer creation..')
        self.optimizer = torch.optim.Adam(params=self.model.parameters(), lr=config['learning_rates'][0])

    def get_train_validation_data(self, train_size=.80, random_state=42):
        train, validation = train_test_split(self.NER_data_df[['doi', 'text', 'entities']], train_size=train_size,
                                             random_state=random_state)
        self.training_data_df = train.reset_index(drop=True)
        self.validation_data_df = validation.reset_index(drop=True)

        print("FULL Dataset: {}".format(self.NER_data_df.shape))
        print("TRAIN Dataset: {}".format(self.training_data_df.shape))
        print("VALIDATION Dataset: {}".format(self.validation_data_df.shape))
        print(' ')

    def data_df2dataset(self):
        training_set = dataset(dataframe=self.training_data_df,
                               tokenizer=self.tokenizer,
                               max_len=self.config['max_length'],
                               get_wids=False,
                               label_all_tokens=self.config['label_all_tokens'])
        validating_set = dataset(dataframe=self.validation_data_df,
                                 tokenizer=self.tokenizer,
                                 max_len=self.config['max_length'],
                                 get_wids=True,
                                 label_all_tokens=self.config['label_all_tokens'])
        return (training_set, validating_set)

    def data_df2dataloader(self):
        training_set, validating_set = self.data_df2dataset()
        self.training_loader = DataLoader(training_set, **self.train_params)
        self.validating_loader = DataLoader(validating_set, **self.valid_params)

    def train_epoch(self, show_every=2000):
        tr_loss, tr_accuracy = 0, 0
        nb_tr_examples, nb_tr_steps = 0, 0
        self.model.train()
        loss_metric = []
        accuracy_metric = []
        step_metrics = []
        for idx, batch in enumerate(self.training_loader):
            ids, mask, labels = get_ids_mask_labels(batch=batch, device=self.config['device'])

            loss, tr_logits = self.model(input_ids=ids, attention_mask=mask, labels=labels,
                                         return_dict=False)
            tr_loss += loss.item()
            nb_tr_steps += 1
            nb_tr_examples += labels.size(0)

            if idx % show_every == 0:
                loss_step = tr_loss / nb_tr_steps
                tr_accuracy = tr_accuracy / nb_tr_steps
                print("Step : {} -- Loss : {} -- Accuracy : {}".format(idx,np.round(loss_step,2),np.round(tr_accuracy,2)))

            if idx%50==0:
                loss_step = tr_loss / nb_tr_steps
                tr_accuracy = tr_accuracy / nb_tr_steps
                loss_metric.append(np.round(loss_step,2))
                accuracy_metric.append(np.round(tr_accuracy,2))
                step_metrics.append(idx)
            flattened_labels, flattened_predictions = flatten_labels_and_predictions(self.model, labels, tr_logits)

            # accuracy computation
            active_accuracy = labels.view(-1) != -100  # shape (batch_size, seq_len)

            labels = torch.masked_select(flattened_labels, active_accuracy)
            predictions = torch.masked_select(flattened_predictions, active_accuracy)

            tmp_tr_accuracy = accuracy_score(labels.cpu().numpy(), predictions.cpu().numpy())
            tr_accuracy += tmp_tr_accuracy
            # gradient clipping
            torch.nn.utils.clip_grad_norm_(
                parameters=self.model.parameters(), max_norm=self.config['max_grad_norm'])

            # backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
        return [np.mean(loss_metric),np.mean(accuracy_metric)]

    def train(self, epochs=0, show_every=2000):
        if epochs == 0:
            epochs = self.config['epochs']
        loss_list,accuracy_list,epoch_list = [],[],[]
        for epoch in tqdm(range(epochs)):
            print('- Epoch : ', epoch)
            for decay in self.optimizer.param_groups:
                decay['lr'] = self.config['learning_rates'][epoch]
            lr = self.optimizer.param_groups[0]['lr']
            result= self.train_epoch(show_every=show_every)
            loss_list.append(result[0])
            accuracy_list.append(result[1])
            epoch_list.append(epoch)
            torch.cuda.empty_cache()
            gc.collect()
        return {'loss': loss_list,
                'accuracy': accuracy_list,
                'epoch': epoch_list}

    def predict_batch(self, batch):

        # MOVE BATCH TO GPU AND INFER
        ids, mask, outputs = get_ids_mask_labels(batch=batch, device=self.config['device'], labels_from_data=False,
                                                 model=self.model)
        all_preds = torch.argmax(outputs[0], axis=-1).cpu().numpy()

        # INTERATE THROUGH EACH TEXT AND GET PRED
        predictions = []
        for k, text_preds in enumerate(all_preds):
            token_preds = [self.ids2labels[i] for i in text_preds]

            prediction = []
            word_ids = batch['wids'][k].numpy()
            previous_word_idx = -1
            for idx, word_idx in enumerate(word_ids):
                if word_idx == -1:
                    pass
                elif word_idx != previous_word_idx:
                    prediction.append(token_preds[idx])
                    previous_word_idx = word_idx
            predictions.append(prediction)
        return predictions

    def get_predictions(self, data_df, data_loader):
        self.model.eval()  # evaluation mode

        y_pred = []
        for batch in data_loader:
            labels = self.predict_batch(batch)
            y_pred.extend(labels)

        final_preds = []
        for i in range(len(data_df)):
            idx = data_df.doi.values[i]
            pred = y_pred[i]  # Leave "B" and "I"
            preds = []
            j = 0
            while j < len(pred):
                cls = pred[j]
                if cls == 'O':
                    j += 1
                else:
                    cls = cls.replace('B', 'I')  # spans start with B
                end = j + 1
                while end < len(pred) and pred[end] == cls:
                    end += 1

                if cls != 'O' and cls != '' and end - j > 7:
                    final_preds.append((idx, cls.replace('I-', ''),
                                        ' '.join(map(str, list(range(j, end))))))

                j = end

        oof = pd.DataFrame(final_preds)
        oof.columns = ['doi', 'class', 'predictionstring']
        return oof

    def compute_validation_F1_score(self):
        oof = self.get_predictions(self.validation_data_df, self.validating_loader)
        f1s = []
        CLASSES = oof['class'].unique()
        print()
        for c in CLASSES:
            pred_df = oof.loc[oof['class'] == c].copy()
            gt_df = self.detailed_data_df.loc[self.detailed_data_df['class'] == c].copy()
            f1 = score_feedback_comp(pred_df, gt_df)
            print(c, f1)
            f1s.append(f1)
        print()
        print('Overall', np.mean(f1s))
        print()