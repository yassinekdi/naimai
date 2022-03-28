from collections import Counter
from transformers import Trainer
import re
import numpy as np
import pandas as pd
from naimai.utils.transformers import score_feedback_comp
from naimai.constants.models import ner_labels, output_labels
from naimai.constants.paths import path_detailed_data

class Predictions_preparer:
    '''
    transform prediction to pandas to use new metric for scoring
    '''

    def __init__(self, predictions, tokenizer, datasets):
        ''' predictions = tensor([[1,2,3], [6,5,1]]) & classifier'''
        self.predictions = predictions
        self.predictions_df = None
        self.tokenizer = tokenizer
        self.datasets = datasets
        self.ids2labels = {k: v for k, v in enumerate(output_labels)}

    def remove_tokenization_effect(self, prediction, tokens):
        '''
        when tokenized, sub words are labelled too and we end up with more word ids than the input. We remove this tokenization effect here and return the prediction filtered
        :param prediction:
        :param tokens:
        :return:
        '''
        encoding = self.tokenizer(tokens, truncation=True, is_split_into_words=True, return_tensors='pt').to('cuda')

        predictions_list = prediction.tolist()
        predictions_filtered = []
        words_ids = encoding.word_ids()
        previous_word_id = None
        for idx, word_id in enumerate(words_ids):
            if word_id is None:
                pass
            elif word_id != previous_word_id:
                predictions_filtered.append(predictions_list[idx])
                previous_word_id = word_id
        return predictions_filtered

    def prediction_filtered2named_labels(self, prediction_filtered):
        '''
        convert prediction ids to named labels
        :param prediction_filtered:
        :return:
        '''
        return [self.ids2labels[elt] for elt in prediction_filtered]

    def clean_named_labels(self, named_labels):
        '''
        remove the initial B- & I- from labels
        :param named_labels: list named labels
        :return:
        '''
        result = [re.sub('[BI]\-', '', elt) for elt in named_labels]
        result = [elt.replace('O', 'other') for elt in result]
        return result

    def get_wids_classes(self, clean_labels):
        '''
        get word ids (or predictionstring) and classes from clean labels
        :param clean_labels:
        :return:
        '''
        cnt = Counter(clean_labels)
        list_prediction_string = []
        classes = []
        for key in cnt:
            prediction_string = [str(idx + 1) for idx, elt in enumerate(clean_labels) if elt == key]
            list_prediction_string.append(' '.join(prediction_string))
            classes.append(key)
        return {'class': classes, 'predictionstring': list_prediction_string}

    def to_df(self, doi, wids_classes):
        '''
         clf.trainer.eval_dataset['doi']
        :param doi:
        :param wids_classes:
        :return:
        '''
        wids_classes['doi'] = [doi] * len(wids_classes['class'])
        return pd.DataFrame(wids_classes)

    def prepare(self):
        list_df = []
        for prediction, dataset in zip(self.predictions, self.datasets):
            doi, tokens = dataset['doi'], dataset['tokens']
            prediction_filtered = self.remove_tokenization_effect(prediction, tokens)
            prediction_named = self.prediction_filtered2named_labels(prediction_filtered)
            clean_prediciton_named = self.clean_named_labels(prediction_named)
            wids_classes = self.get_wids_classes(clean_prediciton_named)
            df = self.to_df(doi, wids_classes)
            list_df.append(df)
        self.predictions_df = pd.concat(list_df)


class BOMR_Trainer(Trainer):

    def __init__(self ,*args ,**kwargs):
        super().__init__(*args ,**kwargs)

    def evaluation_loop(
            self,
            dataloader,
            description,
            prediction_loss_only = None,
            ignore_keys = None,
            metric_key_prefix = "eval",
    ):
        eval_output = super().evaluation_loop(
            dataloader,
            description,
            prediction_loss_only,
            ignore_keys,
            metric_key_prefix
        )

        eval_dataset = self.eval_dataset
        # new_metrics = {}
        is_in_eval = metric_key_prefix == "eval"
        if is_in_eval:
            predictions = eval_output.predictions.argmax(-1)
            preparer = Predictions_preparer(predictions=predictions,
                                            tokenizer=self.tokenizer,
                                            datasets=eval_dataset)

            preparer.prepare()
            eval_pred_df = preparer.predictions_df
            ground_truth_df = pd.read_csv(path_detailed_data).dropna()
            eval_gt_df = ground_truth_df[ground_truth_df["doi"].isin(eval_dataset["doi"])].reset_index(drop=True).copy()

            list_class_f1scores = []
            for class_ in ner_labels:
                gt_df = eval_gt_df.loc[eval_gt_df['class'] == class_].copy()
                pred_df = eval_pred_df.loc[eval_pred_df['class'] == class_].copy()
                f1_score = score_feedback_comp(pred_df, gt_df)
                eval_output.metrics[f"eval_F1-{class_}"] =f1_score
                # new_metrics[f"eval_F1-{class_}"] =f1_score
                list_class_f1scores.append(f1_score)

            eval_output.metrics["eval_F1-avg"] = np.mean(list_class_f1scores)
            # new_metrics["eval_F1-avg"] = np.mean(list_class_f1scores)
        return eval_output
        # return EvalLoopOutput(predictions = eval_output.predictions,
        #                       label_ids = eval_output.label_ids,
        #                       metrics=new_metrics,
        #                       num_samples=eval_output.num_samples)