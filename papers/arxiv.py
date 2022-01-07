import os
from tqdm.notebook import tqdm
from paper2.utils import year_from_arxiv_fname
from paper2.papers.raw import papers, paper
from paper2.utils import replace_abbreviations
from paper2.decorators import paper_reading_error_log_decorator



class papers_arxiv(papers):
    def __init__(self, pdfs_dir, metadata_df, obj_classifier_model=None, author_classifier_model=None,
                 load_obj_classifier_model=True, load_author_classifier_model=False, load_nlp=True):
        super().__init__(pdfs_dir=pdfs_dir,obj_classifier_model=obj_classifier_model, author_classifier_model=author_classifier_model,
                         load_obj_classifier_model=load_obj_classifier_model,
                         load_author_classifier_model=load_author_classifier_model,
                         load_nlp=load_nlp)
        cols = list(metadata_df.columns[:4])
        df = metadata_df[cols].compute()
        self.titles= list(df['title'])
        self.authors= list(df['authors_parsed'])
        self.abstracts= list(df['abstract'])
        self.files_ids = list(df['id'])

    # @paper_reading_error_log_decorator
    def add_paper(self,pdf_filename,idx,use_ocr=False,save_dict=True,report=True):
            pdf_path = self.pdfs_dir + '/' + pdf_filename
            new_paper = paper(path=pdf_path,
                              obj_classifier_model=self.obj_classifier_model)
            new_paper.database='arxiv'
            # new_paper.read_pdf(use_ocr)
            new_paper.Abstract = self.abstracts[idx].replace('-\n', '').replace('\n', ' ')
            new_paper.Title = self.titles[idx].replace('-\n', '').replace('\n', ' ')
            new_paper.Authors = ', '.join([' '.join(at[::-1]) for at in self.authors[idx]])
            new_paper.Publication_year = year_from_arxiv_fname(pdf_filename)
            # if new_paper.converted_text:
                # new_paper.get_Introduction(portion=portion)
                # new_paper.get_Conclusion()
                # new_paper.get_kwords()
            new_paper = replace_abbreviations(new_paper)
            new_paper.get_objective_paper()
            if report:
                new_paper.report_objectives()
            if save_dict:
                self.elements[new_paper.file_name] = new_paper.save_paper_for_training()
                self.naimai_elements[new_paper.file_name] = new_paper.save_paper_for_naimai()
            else:
                self.elements[new_paper.file_name] = new_paper

    def get_papers(self,portion=1/6,list_files=[],path_chunks='',use_ocr=False,save_dict=True, report=True):
        if list_files:
            all_files = list_files
        else:
            all_files = self.files_ids
            # all_files = sorted(os.listdir(self.pdfs_dir))
        idx=0
        for pdf_filename in tqdm(all_files):
            # if 'pdf' in pdf_filename:
            try:
                self.add_paper(pdf_filename,idx,use_ocr=use_ocr,save_dict=save_dict,report=report)
            except:
                pass
            if idx % 500 == 0 and path_chunks:
                print('  Saving idx {} for filename {}'.format(idx, pdf_filename))
                self.save(path_chunks)
            idx += 1
        print('Objs problem exported in objectives_pbs.txt')