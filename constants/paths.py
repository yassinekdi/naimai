import os


# if 'win' in platform:
#         path_nlp=r'paper2\deps\spacy_Ner_data'
#         path_encoder = r'paper2\deps\encoder.pkl'
#         path_objective_classifier=r'paper2\models\papers_classification\objective classif'
#         path_author_classifier = r'paper2\models\papers_classification\authors classif\authors_classif_GP'
#         path_main_pipelines = r'main_pipelines_dir'
# else:


path_nlp = os.path.join('paper2','deps','SpaCy_Ner_data')
path_encoder = 'drive/MyDrive/MyProject/data/Intent_classif_data/distil_bert_obj_classifier'
path_objective_classifier = os.path.join('paper2','models','papers_classification','objective classif')
path_main_pipelines = os.path.join('main_pipelines_dir')
path_author_classifier = os.path.join('paper2','models','papers_classification','authors classif','authors_classif_GP')


path_google_search='https://google.com/search?q='
path_errors_log = 'drive/MyDrive/MyProject/errors_log/'
path_model_saving= 'drive/MyDrive/MyProject/models/PDF classif/'

aws_root_pdfs = 'https://naimabucket.s3.amazonaws.com/PDFs/'
Mybucket = "naimabucket"
arxiv_database='arxiv'