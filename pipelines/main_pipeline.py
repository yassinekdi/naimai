import os
from paper2.crawlers.arxiv_crawler import ArXiv_Crawler
from paper2.papers.arxiv import papers_arxiv
from paper2.papers.raw import papers
from paper2.constants import arxiv_database
from paper2.models.papers_classification.tfidf import tfIdf_model

class MainPipeline:
    def __init__(self,database='',pdfs_dir='',params=[], papers=None, model=None,get_ArXiv_manifest=True):
        # if database = '' -> params = []
        # if database = 'arxiv' -> params = [path_arxiv_json_data (str), pdf_manifest_dir (str), category (str))]
        self.pdfs_dir = pdfs_dir
        self.params = params
        self.not_downloaded=[]
        self.papers=papers
        self.crawler = None
        self.model = model

        if database == arxiv_database and len(self.params)==4:
            self.database = database
            arxiv_metadata_dir, pdf_manifest_dir, tar_dir, self.arxiv_category = self.params
            self.crawler = ArXiv_Crawler(arxiv_metadata_dir=arxiv_metadata_dir, pdfs_dir=self.pdfs_dir, tar_dir=tar_dir
                                         ,pdf_manifest_dir=pdf_manifest_dir,category=self.arxiv_category,
                                         get_manifest=get_ArXiv_manifest)
        else:
            self.arxiv_category=''
            self.database = database

    def download_arxiv_data(self):
            self.crawler.download_tar_files()

    def create_papers_arxiv(self,portion=1/3, path_chunks='',start_idx=0,use_ocr=False):
        print('  Getting category docs ..')
        self.crawler.get_category_docs(take_all_category_files=False,category=self.arxiv_category)
        print('  Docs 2 df ..')
        metadata_df = self.crawler.docs2df()
        print('  Creating papers object ..')
        all_papers = papers_arxiv(self.pdfs_dir, metadata_df)
        ids = list(metadata_df['id'])
        list_files = [elt+'.pdf' for elt in ids][start_idx:]
        all_papers.get_papers(portion=portion, list_files=list_files,
                              path_chunks=path_chunks+'/all_papers_temp_'+self.arxiv_category, use_ocr=use_ocr)
        return all_papers

    def create_papers_raw(self,portion=1/3, path_chunks='',use_ocr=False):
        all_papers = papers(self.pdfs_dir)
        all_papers.get_papers(portion=portion, path_chunks=path_chunks+'/all_papers_temp',use_ocr=use_ocr)
        return all_papers

    def create_papers(self,portion=1/3, path_chunks='', start_idx=0, use_ocr=False):
        if self.database==arxiv_database:
            self.papers = self.create_papers_arxiv(portion=portion, path_chunks=path_chunks, start_idx=start_idx,use_ocr=use_ocr)
        else:
            self.papers = self.create_papers_raw(portion=portion, path_chunks=path_chunks,use_ocr=use_ocr)

    def update_papers(self,portion=1/3):
        files = os.listdir(self.pdfs_dir)
        existing_files = [self.papers[fname].file_name for fname in self.papers.elements]
        files_to_add = [elt for elt in files if elt not in existing_files]
        self.papers.get_papers(portion=portion, list_files=files_to_add)

    def save_papers(self,papers_name):
        self.papers.save(papers_name)

    def create_classifier(self,save_every=False,path_save_chunks='',start_idx=0):
        all_papers_list = [self.papers.elements[elt] for elt in self.papers.elements]
        self.model = tfIdf_model(all_papers_list, shuffle=True)
        self.model.get_documents()
        print('   Building vocab with tfidf model..')
        self.model.build_corpus(save_chunks=save_every, path_save_chunks=path_save_chunks, start_idx=start_idx)

    def update_classifier(self):
        if self.model:
            self.model.update_docs_and_corpus(self.papers)

    def train_classifier(self):
        self.model.vectorizer.min_df=0.05
        self.model.train()

    def save_classifier_encodings(self, classifier_name):
        self.model.save_encodings(classifier_name)

    def save_classifier(self,classifier_name):
        self.model.save_model(classifier_name)

    def get(self,update=False,portion=1/4,main_pipeline_dir='',save_models=True,use_ocr=False):
        if save_models:
            if not os.path.isdir(main_pipeline_dir):
                os.mkdir(main_pipeline_dir)

        print('>>> Analyzing PDFs ..')
        if update:
            self.update_papers(portion=portion)
        else:
            self.create_papers(portion=portion, path_chunks=main_pipeline_dir,use_ocr=use_ocr)

        if save_models:
            print('>>> Saving the papers in ', main_pipeline_dir)
            self.save_papers(main_pipeline_dir+'/all_papers')

        if update:
            print('>>> Updating the classifier, tfidf as default model')
            self.update_classifier()
        else:
            print('>>> Creating the classifier, tfidf as default model')
            self.create_classifier(save_every=False)

        print('>>> Training the classifier')
        self.train_classifier()

        if save_models:
            print('>>> Saving encodings in ', main_pipeline_dir)
            self.save_classifier_encodings(main_pipeline_dir + '/document_term_matrix.gzip')

            print('>>> Saving classifier ', main_pipeline_dir)
            self.save_classifier(main_pipeline_dir + '/tfmodel')

        print(">>> Done! Let's go !!")






