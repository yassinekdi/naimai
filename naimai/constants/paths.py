import os

grobid_url = "https://cloud.science-miner.com/grobid"
path_nlp = 'drive/MyDrive/MyProject/paper2/deps/SpaCy_Ner_data'
path_objective_classifier = 'naimai4science/objective-classifier-v0'
path_bomr_classifier = 'naimai4science/bomr-classifier-v0'
path_main_pipelines = os.path.join('main_pipelines_dir')
path_author_classifier = os.path.join('paper2','models','papers_classification','authors classif','authors_classif_GP')
codes_fields_path = "drive/MyDrive/MyProject/data_pipeline/landing_zone/Elsevier_Open_Journals/ASJC.xlsx"
naimai_dois_path = "drive/MyDrive/MyProject/data_pipeline/naimai_zone/naimai_dois"
path_formatted='drive/MyDrive/MyProject/data_pipeline/naimai_zone/Formatted_data/'
path_dispatched = 'drive/MyDrive/MyProject/data_pipeline/naimai_zone/Dispatched_data/'
path_produced = 'drive/MyDrive/MyProject/data_pipeline/naimai_zone/Production_data/'
path_similarity_model = os.path.join('drive/MyDrive/MyProject/data_pipeline','search_model')

path_google_search='https://google.com/search?q='
path_errors_log = 'drive/MyDrive/MyProject/errors_log/'
path_model_saving= 'drive/MyDrive/MyProject/models/PDF classif/'
path_open_citations = 'https://opencitations.net/index/coci/api/v1/citations/'

aws_root_pdfs = 'https://naimabucket.s3.eu-west-3.amazonaws.com/PDFs/'
Mybucket = "naimabucket"
arxiv_pdfs_url = 'https://arxiv.org/pdf/'

training_data_path = 'drive/MyDrive/MyProject/main_pipelines/all/total_training_papers'
naimai_data_path = 'drive/MyDrive/MyProject/main_pipelines/all/total_naimai_papers'
doi_url = 'https://www.doi.org/'

path_detailed_data = "drive/MyDrive/MyProject/data/Intent_classif_data/detailed_data.csv"
path_detailed_data_0_500= "drive/MyDrive/MyProject/data/Intent_classif_data/detailed_data_0-500.csv"
path_detailed_data_500_1000= "drive/MyDrive/MyProject/data/Intent_classif_data/detailed_data_500-1000.csv"
path_detailed_data_total = "drive/MyDrive/MyProject/data/Intent_classif_data/detailed_data_total.csv"

path_ner_data = "drive/MyDrive/MyProject/data/Intent_classif_data/NER_data_df.csv"
path_ner_balanced_data = "drive/MyDrive/MyProject/data/Intent_classif_data/path_ner_balanced_data.csv"
path_ner_balanced_data2 = "drive/MyDrive/MyProject/data/Intent_classif_data/path_ner_balanced_data2.csv"
path_ner_data_reduced = "drive/MyDrive/MyProject/data/Intent_classif_data/NER_data_reduced.csv"
path_ner_data_500_1000= "drive/MyDrive/MyProject/data/Intent_classif_data/NER_data_df_500-1000.csv"
path_ner_data_0_500= "drive/MyDrive/MyProject/data/Intent_classif_data/NER_data_df_0-500.csv"
path_ner_data_total = "drive/MyDrive/MyProject/data/Intent_classif_data/NER_data_df_total.csv"