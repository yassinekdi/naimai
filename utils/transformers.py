import torch
from sklearn.metrics import classification_report
from spacy import displacy
from naimai.constants.models import colors_labels
import numpy as np
from naimai.constants.models import output_labels
from datasets import load_metric
import pandas as pd

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


def sklearn_scores(labels,predictions):
  scores=classification_report(labels,predictions, output_dict=True, zero_division=0)
  result = {'f1 macro avg': scores['macro avg']['f1-score'],
            'accuracy': scores['accuracy']}
  return result

def get_ids_mask_labels(batch,device,labels_from_data=True, model=None):
  ids = batch['input_ids'].to(device, dtype = torch.long)
  mask = batch['attention_mask'].to(device, dtype = torch.long)
  if labels_from_data:
    labels = batch['labels'].to(device, dtype = torch.long)
  else:
    labels = model(ids, attention_mask=mask, return_dict=False)
  return (ids,mask,labels)

def flatten_labels_and_predictions(model,labels,tr_logits):
  flattened_labels = labels.view(-1) # shape (batch_size * seq_len,)
  active_logits = tr_logits.view(-1, model.num_labels) # shape (batch_size * seq_len, num_labels)
  flattened_predictions = torch.argmax(active_logits, axis=1) # shape (batch_size * seq_len,)
  return (flattened_labels,flattened_predictions)


def calc_overlap(row):
    """
    Calculates the overlap between prediction and
    ground truth and overlap percentages used for determining
    true positives.
    """
    set_pred = set(row.predictionstring_pred.split(' '))
    set_gt = set(row.predictionstring_gt.split(' '))
    # Length of each and intersection
    len_gt = len(set_gt)
    len_pred = len(set_pred)
    inter = len(set_gt.intersection(set_pred))
    overlap_1 = inter / len_gt
    overlap_2 = inter / len_pred
    return [overlap_1, overlap_2]


def score_feedback_comp(pred_df, gt_df):
    """
    Modified function that scores for the kaggle
        Student Writing Competition

    Uses the steps in the evaluation page here:
        https://www.kaggle.com/c/feedback-prize-2021/overview/evaluation
    """
    gt_df = gt_df[['doi', 'class', 'predictionstring']].reset_index(drop=True).copy()
    pred_df = pred_df[['doi', 'class', 'predictionstring']].reset_index(drop=True).copy()
    pred_df['pred_id'] = pred_df.index
    gt_df['gt_id'] = gt_df.index
    # Step 1. all ground truths and predictions for a given class are compared.
    joined = pred_df.merge(gt_df,
                           left_on=['doi', 'class'],
                           right_on=['doi', 'class'],
                           how='outer',
                           suffixes=('_pred', '_gt')
                           )
    joined['predictionstring_gt'] = joined['predictionstring_gt'].fillna(' ')
    joined['predictionstring_pred'] = joined['predictionstring_pred'].fillna(' ')

    joined['overlaps'] = joined.apply(calc_overlap, axis=1)

    # 2. If the overlap between the ground truth and prediction is >= 0.5,
    # and the overlap between the prediction and the ground truth >= 0.5,
    # the prediction is a match and considered a true positive.
    # If multiple matches exist, the match with the highest pair of overlaps is taken.
    joined['overlap1'] = joined['overlaps'].apply(lambda x: eval(str(x))[0])
    joined['overlap2'] = joined['overlaps'].apply(lambda x: eval(str(x))[1])

    joined['potential_TP'] = (joined['overlap1'] >= 0.5) & (joined['overlap2'] >= 0.5)
    joined['max_overlap'] = joined[['overlap1', 'overlap2']].max(axis=1)
    tp_pred_ids = joined.query('potential_TP') \
        .sort_values('max_overlap', ascending=False) \
        .groupby(['doi', 'predictionstring_gt']).first()['pred_id'].values

    # 3. Any unmatched ground truths are false negatives
    # and any unmatched predictions are false positives.
    fp_pred_ids = [p for p in joined['pred_id'].unique() if p not in tp_pred_ids]

    matched_gt_ids = joined.query('potential_TP')['gt_id'].unique()
    unmatched_gt_ids = [c for c in joined['gt_id'].unique() if c not in matched_gt_ids]

    # Get numbers of each type
    TP = len(tp_pred_ids)
    FP = len(fp_pred_ids)
    FN = len(unmatched_gt_ids)
    # calc microf1
    my_f1_score = TP / (TP + 0.5 * (FP + FN))

    return my_f1_score


def split_list(lst) -> list:
    '''
    split list lst into list of sequences retrieved in lst
    :param lst:
    :return:
    '''
    preceding_elt = lst[0]
    new_starting_idxs = []
    for idx, elt in enumerate(lst[1:]):
        if elt == preceding_elt + 1:
            preceding_elt = elt
        else:
            new_starting_idxs.append(idx + 1)
            preceding_elt = elt

    if new_starting_idxs:
        first_elt = lst[0]
        new_list = []
        for idx in new_starting_idxs:
            ls_ = list(np.arange(first_elt, lst[idx - 1] + 1))
            new_list.append(ls_)
            try:
                first_elt = lst[idx + 1] - 1
            except:
                first_elt = lst[idx]
        last_elt = list(np.arange(first_elt, lst[-1] + 1))
        new_list.append(last_elt)

        return new_list
    else:
        return [lst]

def process_predictionstring(elt):
  # process predictionstring column to split lists into sequences
  list_pstring = list(map(int,elt.split()))
  list_processed = split_list(list_pstring)
  return list_processed

def list2pstring(lst):
  # convert list to predictionstring format
  lst_str = list(map(str,lst))
  return ' '.join(lst_str)

def process_df(df):
  # transform original df into df with splitted predictionstring following sequences
  new_dict = {'class': [], 'new_pstring':[]}
  df['pstring_processed']=df['predictionstring'].apply(process_predictionstring)
  for idx in range(len(df)):
    elts = df.iloc[idx]
    classe = elts['class']
    new_pstrings = elts['pstring_processed']
    if len(new_pstrings)==1:
      pstring_elt = new_pstrings[0]
      new_dict['class'].append(classe)
      list_pstring = list2pstring(pstring_elt)
      new_dict['new_pstring'].append(list_pstring)
    else:
      for elt in new_pstrings:
        if elt:
          new_dict['class'].append(classe)
          list_pstring = list2pstring(elt)
          new_dict['new_pstring'].append(list_pstring)
  new_df = pd.DataFrame(new_dict)
  return new_df

def get_first_char_id(elt,text):
  start_wd = elt['start']
  split=text.split()
  first_wds = ' '.join(split[start_wd:start_wd+5])
  first_char = text.index(first_wds)
  return first_char

def get_last_char_id(elt,text):
  end_wid = elt['end']
  split=text.split()
  last_wds = ' '.join(split[end_wid-5:end_wid])
  end_char = text.index(last_wds)+len(last_wds)
  return end_char

def get_doc_options(txt, old_df):
    df = process_df(old_df)
    df['start'] = df['new_pstring'].apply(lambda x: int(x.split()[0]) - 1)
    df['end'] = df['new_pstring'].apply(lambda x: int(x.split()[-1]))
    df['start_char'] = df.apply(get_first_char_id, args=(txt,), axis=1)
    df['last_char'] = df.apply(get_last_char_id, args=(txt,), axis=1)
    df = df.sort_values(by=['start'])

    labels_list = df['class'].tolist()
    labels_list = [elt[:3].upper() for elt in labels_list]
    start_list = df['start_char'].tolist()
    end_list = df['last_char'].tolist()

    ents = []
    colors = {label: colors_labels[label] for label in labels_list}
    for start, end, label in zip(start_list, end_list, labels_list):
        dic = {'start': start, 'end': end, 'label': label}
        ents.append(dic)

    doc = {'text': txt, "ents": ents}
    options = {'ents': labels_list, "colors": colors}
    return {'doc': doc, "options": options}


def visualize(txt, df,show=True):
    '''
    Visualize segmented text in data frame df using displacy
    :param txt:
    :param df:
    :return:
    '''
    results = get_doc_options(txt, df)
    if show:
        doc = results['doc']
        options = results['options']
        displacy.render(doc, style="ent", options=options, manual=True, jupyter=True)

def get_text(elt,txt):
    '''
    used in df.apply to extract text using start char and last char of predicted classes.
    :param elt:
    :param txt:
    :return:
    '''
    start_char = elt['start_char']
    last_char = elt['last_char']
    return txt[start_char:last_char]
