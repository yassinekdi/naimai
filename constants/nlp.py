nlp_disabled_processing = ["tok2vec", "parser", "attribute_ruler", 'entity_ruler','textcat','textcar_multilabel','morphologizer','senticizer','transformer']
nlp_disabled_direct2reported = ["tok2vec", "attribute_ruler", 'entity_ruler','textcat','textcar_multilabel','morphologizer','senticizer','transformer', "ner"]

nlp_vocab = 'en_core_web_sm'

past_tense='VBD'
verb_pos='VERB'
root_dep='ROOT'
conj_dep = 'conj'

this_year=2021
max_len_objective_sentence = 45