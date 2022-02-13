import re
import random
import pickle
import os
from tqdm.notebook import tqdm
import spacy
from naimai.processing import SentenceToProcess
from naimai.utils import convert_pdf_to_txt, get_pattern, \
    str1_str2_from_txt, filter_min_length, starts_with_capital, doi_in_text, get_duplicates, multiple_replace, \
    clean_objectives, clean_authors, year_from_arxiv_fname, replace_abbreviations, load_gzip, save_gzip
from naimai.constants.regex import regex_email, regex_not_converted,regex_references, regex_abstract1, \
    regex_abstract2, regex_words_numbers_some, regex_cid, regex_objectives,regex_paper_year,regex_filtered_words_obj
from naimai.constants.replacements import parsing_corrections
from naimai.constants.paths import path_objective_classifier, path_errors_log, path_author_classifier, path_encoder, naimai_dois_path
from naimai.constants.nlp import this_year, nlp_vocab, max_len_objective_sentence
from naimai.models.abbreviation import extract_abbreviation_definition_pairs
# from naimai.classifiers import Objective_classifiers
# from naimai.models.text_generation.paper2reported import Paper2Reported
#from naimai.decorators import paper_reading_error_log_decorator

class paper_base:
    def __init__(self):
        self.pdf_path=''
        self.database='raw'
        self.file_name = ''
        self.raw_text = ''
        self.fields = []
        self.numCitedBy = .5
        self.numCiting = .5
        self.Introduction = ''
        self.Abstract = ''
        self.Conclusion = ''
        self.Keywords = ''
        self.Authors = ''
        self.Title = ''
        self.year = 999
        self.References = []
        self.Emails = []
        self.doi = ''


    def get_abbreviations_dict(self):
        abstract_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Abstract)
        intro_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Introduction)
        conclusion_abbrevs = extract_abbreviation_definition_pairs(doc_text=self.Conclusion)
        abstract_abbrevs.update(intro_abbrevs)
        abstract_abbrevs.update(conclusion_abbrevs)

        corrected_abbrevs = {}
        for k in abstract_abbrevs:
            corrected_abbrevs[' ' + k] = ' ' + abstract_abbrevs[k] + ' ' + '(' + k + ')'
        return corrected_abbrevs

    def is_in_database(self,list_dois):
        if self.doi in list_dois:
            return True
        return False

    def save_dict(self):
        attr_to_save = ['doi', 'Authors', 'year','database','fields','Abstract','Keywords', 'Title','numCitedBy','numCiting']
        paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
        return paper_to_save

    # def save_paper_for_naimai(self):
    #     attr_to_save = ['file_name', 'doi', 'Objectives_reported', 'database']
    #     paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
    #     return paper_to_save
    #
    #
    # def save_paper_for_training(self):
    #     attr_to_save = ['pdf_path', 'file_name', 'Abstract', 'Conclusion', 'Keywords', 'Title','database']
    #     paper_to_save = {key: self.__dict__[key] for key in attr_to_save}
    #     return paper_to_save



class paper(paper_base):

    def __init__(self, path=''):
        super().__init__()
        self.pdf_path = path
        self.file_name = self.pdf_path.split('/')[-1]
        self.intro_term = 'introduction'
        self.abstract_term = 'abstract'
        self.references_term = 'references'
        self.conclusion_term  = 'conclusion'
        self.path_errors_log = path_errors_log
        self.Citations=[]
        # self.author_classifier_model=author_classifier_model
        self.converted_text=''



    def pdf2text(self,use_ocr):
        converted_text = convert_pdf_to_txt(self.pdf_path, is_path=True,use_ocr=use_ocr)
        text_without_cid = re.sub(regex_cid, '', converted_text)
        if text_without_cid:
            self.converted_text = text_without_cid


    def read_pdf(self,use_ocr=False):
        # pdf to raw text
        self.pdf2text(use_ocr)
        if self.converted_text:
            text_only_wordsNnumbers = re.sub(regex_words_numbers_some, '', self.converted_text)
            text_only_wordsNnumbers=re.sub(regex_not_converted, '', text_only_wordsNnumbers)
            duplicated_sentences = get_duplicates(text_only_wordsNnumbers, 5)

            for sentence in duplicated_sentences:
                text_only_wordsNnumbers = text_only_wordsNnumbers.replace(sentence, '')
            text_only_wordsNnumbers=text_only_wordsNnumbers.replace('-\n', '').replace('\n', ' ')

            abbreviations_dic = extract_abbreviation_definition_pairs(doc_text=text_only_wordsNnumbers)
            if abbreviations_dic:
                final_modifs = multiple_replace(abbreviations_dic, text_only_wordsNnumbers)
            else:
                final_modifs = text_only_wordsNnumbers
            self.raw_text = multiple_replace(parsing_corrections,final_modifs)


    def get_Introduction(self, portion=1 / 6):
        """
        assumption : 2.  Introduction is contained in the first portion=1/6 of total lengths of words in paper (1/6 seems to be working in our case : hydraulic)
        :param portion:
        :return:
        """
        headings = self.get_headings()
        if headings:
            headings = self.correct_headings()
            if len(headings)>1:
                nbs = [int(re.findall('\d', elt)[0]) for elt in headings[:2]]
                if nbs[1] == nbs[0] + 1:
                    self.Introduction = str1_str2_from_txt(headings[0], headings[1], self.raw_text)
            else:
                text_after_intro_term = self.get_txt_after_Introduction()
                self.Introduction = self.get_txt_portion(text_after_intro_term, portion)

        if not self.Introduction:
            text_after_intro_term = self.get_txt_after_Introduction()
            self.Introduction = self.get_txt_portion(text_after_intro_term, portion)


    def get_headings(self):
        headings_pattern = get_pattern(self.raw_text)
        headings = []
        if headings_pattern:
            ptrn = re.compile(headings_pattern, flags=re.M | re.I)
            result = re.findall(ptrn, self.raw_text)
            for elt in result:
                # check lengths
                if (len(elt.split(' ')) < 10) and (len(elt.split(' ')) > 1):
                    headings.append(elt)
            checks = [self.intro_term in elt.lower() for elt in headings]
            if True in checks:
                return headings
        # old method
        return


    def correct_headings(self):
        headings = self.get_headings()
        if headings:
            headings = filter_min_length(headings)
            nbs = [int(re.findall('\d', elt)[0]) for elt in headings]
            one_indx = nbs.index(1)
            nbs = nbs[one_indx:]
            srt_idx = []
            idd = 0
            ref = 99
            for idx, nb in enumerate(nbs):
                if nb == 1 and idx == idd:
                    srt_idx.append(idx)
                    ref = 2
                    idd = idx
                else:
                    if ref == nb:
                        srt_idx.append(idx)
                        ref = nbs[idx] + 1
            return [headings[id] for id in srt_idx]
        return


    def get_txt_after_Introduction(self):
        if self.intro_term in self.raw_text.lower():
            pattern = self.intro_term+'(.*?)\n(.*)'
            resl= re.findall(pattern, self.raw_text, flags=(re.I | re.S))
            if resl:
                text_after_intro_term = resl[0][len(resl[0])-1]
            else:
                if self.write_errors:
                    txt_error='Little pb in ' + str(self.file_name) + '\n'
                    with open(self.path_errors_log + 'errors_log.txt', 'a') as f:
                        f.write(txt_error)
                    if self.verbose:
                        print(txt_error)
                text_after_intro_term = self.raw_text
        else:
            if self.write_errors:
                txt_error='No introduction term in ' + str(self.file_name) + '\n'
                with open(self.path_errors_log + 'errors_log.txt', 'a') as f:
                    f.write(txt_error)
                if self.verbose:
                    print(txt_error)
            text_after_intro_term = self.raw_text
        return text_after_intro_term


    def get_txt_portion(self, text_after_intro_term, portion):
        if text_after_intro_term:
            all_words = text_after_intro_term.split(' ')
            threshold = int(len(all_words) * portion)
            return ' '.join(all_words[:threshold])

    def get_Abstract(self):
        intro_in_txt = self.intro_term in self.raw_text.lower()
        self.get_abtract_term()
        abstract=''
        if intro_in_txt:
            if self.abstract_term:
                pattern = self.abstract_term + '(.*?)' + self.intro_term
                abstract = self.get_str_from_txt(pattern, idx=0)
            else:
                patrn = '\n(.*?)' + self.intro_term
                abstract = self.get_str_from_txt(patrn, idx=0)

        if not abstract:
            print('no abstract')

        if abstract:
            split = abstract.split('\n\n')
            lst = [len(elt) for elt in split]
            mx = max(lst)
            idx = lst.index(mx)
            abstract = split[idx]
        self.Abstract = abstract


    def get_abtract_term(self):
        self.abstract_term = self.get_str_from_txt(regex_abstract1, flags=(re.M | re.I), idx=0)

        if not self.abstract_term:
            self.abstract_term = self.get_str_from_txt(regex_abstract2, flags=(re.M | re.I), idx=0)

        if not self.abstract_term:
            self.abstract_term=''


    def get_str_from_txt(self,pattern,flags=(re.I | re.S), idx=-1):
        result= re.findall(pattern, self.raw_text, flags=flags)
        if result:
            return result[idx]
        return


    def get_Conclusion(self,verbose=False):
        try:
            # conclusion term &  next header
            headings = self.get_headings()
            if headings:
                if any(self.conclusion_term in s.lower() for s in headings):
                    conclusion_term = [elt for elt in headings if self.conclusion_term in elt.lower()]
                    if conclusion_term:
                        conclusion_term = conclusion_term[0]
                else:
                    conclusion_term = self.get_str_from_txt('conclusions?')
            else:
                conclusion_term = self.get_str_from_txt('conclusions?')
            next_header = self.header_after_conclusion(headings)

            pattern1 = conclusion_term + '(.*?)' + next_header
            self.Conclusion = self.get_str_from_txt(pattern1, flags=re.S)
            if not self.Conclusion:
                pattern2 = conclusion_term + '(.*)'
                self.Conclusion = self.get_str_from_txt(pattern2, flags=re.S)
        except:
            if verbose:
                print('No conclusion term in ', self.pdf_path)
            pass


    def header_after_conclusion(self, headings):
        next_header = None
        if headings:
            if any(self.conclusion_term in s for s in headings):
                idx_conclusion = [idx for idx, elt in enumerate(headings) if self.conclusion_term in elt][0]
                if len(headings) > idx_conclusion + 1:
                    try:
                        next_header = headings[idx_conclusion + 1]
                        return next_header
                    except:
                        pass

        if not next_header:
            ref_term_in_text = self.get_str_from_txt(self.references_term)
            acknowledgments_in_txt = re.search('acknow?ledge?ments?', self.raw_text, flags=(re.I | re.S))
            if acknowledgments_in_txt:
                next_header = acknowledgments_in_txt.group(0)
            else:
                next_header = ref_term_in_text
            return next_header
        return


    def get_kwords(self):
        kwords_terms = ['key words', 'keywords']
        kwords_term = [elt for elt in kwords_terms if elt in self.raw_text.lower()]
        if kwords_term:
            kwords_term = kwords_term[0]
            idx_kword = self.raw_text.lower().index(kwords_term)

            self.Keywords = self.raw_text[idx_kword:].split('\n\n')[0].lower().replace(kwords_term, '').replace('\n', ' ')
        else:
            if self.write_errors:
                txt_error = 'No key words in ' + str(self.file_name) + '\n'
                with open(self.path_errors_log + 'errors_log.txt', 'a') as f:
                    f.write(txt_error)
                if self.verbose:
                    print(txt_error)


    # def get_author_model(self):
    #     if not self.author_classifier_model:
    #         filehandler = open(path_author_classifier,'rb')
    #         self.author_classifier_model = pickle.load(filehandler)


    def get_references(self, verbose=False):
        regex_nb_first = r'^\[?\(?\d+\)?\]?\.?'
        first_list = re.findall(regex_references, self.raw_text, flags=re.S | re.I)
        if first_list:
            first_refs = [elt for elt in first_list[0].split('\n') if elt]
            first_refs = [re.sub(regex_nb_first,'', elt) for elt in first_refs]
            first_refs = [elt for elt in first_refs]

            first_capital = [starts_with_capital(elt) for elt in first_refs]
            for reference, is_capital in zip(first_refs, first_capital):
                if is_capital:
                    self.References.append(reference)
                else:
                    try:
                        self.References[-1] += ' ' + reference
                    except:
                        if verbose:
                            print('no references in ', self.pdf_path)
                        pass


    def get_doi(self):
        doi = doi_in_text(self.raw_text)
        return doi


    def get_emails(self):
        txt_before_intro = self.get_txt_before_Introduction()
        emails=re.findall(regex_email, txt_before_intro, flags=re.I | re.M)
        if emails:
            self.Emails = emails
        else:
            txt_after_intro = self.get_txt_after_Introduction()
            self.Emails = re.findall(regex_email, txt_after_intro, flags=re.I | re.M)


    def get_citations(self):
        if self.Introduction:
            intro = self.Introduction
            stc=SentenceToProcess(intro)
            self.Citations = stc.get_citations()


    def get_txt_before_Introduction(self):
        split = self.raw_text.lower().split(self.intro_term)
        split2_no_empty = []
        if split:
            txt_before_intro = split[0]
            split2 = txt_before_intro.split('\n')
            split2_no_empty = [elt for elt in split2 if elt]
        result = []
        idx_max = 15
        for idx, elt in enumerate(split2_no_empty):
            self.get_abtract_term()
            if (self.abstract_term in elt) or (idx == idx_max):
                break
            result.append(elt)
        return ' '.join(result)


    # def get_list_sentences_between_intro_abstract(self):
    #     split = self.converted_text.split('\n')
    #
    #     for idx, el in enumerate(split):
    #         if self.abstract_term:
    #             found = re.findall(self.abstract_term + '|' + self.intro_term, el, flags=re.I)
    #         else:
    #             found = re.findall(self.intro_term, el, flags=re.I)
    #         if found:
    #             break
    #     split = split[:idx]
    #     split_without_RF = [elt for elt in split if 'River' not in elt]
    #     split3 = [elt.split(';')[0] for elt in split_without_RF if elt]
    #     split4 = []
    #     if split3:
    #         split4 = [elt for elt in clean_authors(split3) if len(elt) > 2 and not re.findall('Engineer|Proce', elt)]
    #     return split4


    # def get_authors(self):
    #     list_sentences = self.get_list_sentences_between_intro_abstract()
    #     GP = self.author_classifier_model
    #     encodings = [self.encoding_model.encode(stc, convert_to_numpy=True) for stc in list_sentences]
    #     authors_list = []
    #     for idx, encod in enumerate(encodings):
    #         GP_pred = GP.predict([encod])
    #         if GP_pred[0]:
    #             authors_list += [list_sentences[idx].replace(' and', '')]
    #     if authors_list:
    #         authors_list = [' '.join(authors_list)]
    #         self.Authors = re.sub(' [a-zA-Z],| [a-zA-Z] | [a-zA-Z]$', '', authors_list[0])


    def get_year(self):
        years = re.findall(regex_paper_year, self.Introduction)
        years_list=[int(elt) for elt in years]
        if years_list:
            year = max(years_list)
            if year < this_year:
                self.year = year
            else:
                self.year = this_year
        else:
            years = re.findall(regex_paper_year, self.raw_text)
            years_list = [int(elt) for elt in years]
            if years_list:
                year = max(years_list)
                if year < this_year:
                    self.year = year
                else:
                    self.year = this_year


class papers:
    def __init__(self):
        self.elements = {}
        self.naimai_elements = {}
        self.path_errors_log = 'drive/MyDrive/MyProject/errors_log/'
        self.database='mine'
        if os.path.exists(naimai_dois_path):
            self.naimai_dois = load_gzip(naimai_dois_path)
        else:
            self.naimai_dois=[]


    def __len__(self):
        return len(self.elements.keys())

    def __setitem__(self, key, value):
        self.elements[key] = value

    def __getitem__(self, item):
        return self.elements[item]

    def random_papers(self,k=3, seed=None):
        elts = list(self.elements)
        random.seed(seed)
        rds = random.sample(elts, k)
        papers_list = [self.elements[el] for el in rds]
        return papers_list

    # @paper_reading_error_log_decorator
    def add_paper(self,portion=1/6,use_ocr=False):
            new_paper = paper()
            new_paper.read_pdf(use_ocr)
            if new_paper.converted_text:
                new_paper.get_Introduction(portion=portion)
                new_paper.get_Abstract()
                # new_paper.get_authors()
                new_paper.get_Conclusion()
                new_paper.get_year()
                new_paper.get_kwords()
                self.elements[new_paper.file_name] = new_paper.save_dict()
            else:
                self.elements[new_paper.file_name] = "USE OCR"


    def get_papers(self,portion=1/6,list_files=[],path_chunks='',use_ocr=False):
        all_files=[]
        if list_files:
            all_files = list_files

        idx=0
        for file_name in tqdm(all_files):
            if re.findall('pdf', file_name, flags=re.I):
                self.add_paper(portion=portion,use_ocr=use_ocr)
                if idx % 500 == 0 and path_chunks:
                    print('  Saving papers - idx {} for filename {}'.format(idx, file_name))
                    self.save(path_chunks)
                idx+=1
        print('Objs problem exported in objectives_pbs.txt')

    def save_elements(self, file_dir,update=False):
        papers_to_save = self.__dict__['elements']
        if update and os.path.exists(file_dir):
            loaded_papers = load_gzip(file_dir)
            loaded_papers.update(papers_to_save)
            save_gzip(file_dir,loaded_papers)
        else:
            save_gzip(file_dir,papers_to_save)


    def update_naimai_dois(self):
        if self.naimai_dois:
            save_gzip(naimai_dois_path,self.naimai_dois)


# class papers_distil(papers):
#     def __init__(self, all_papers_to_update_dir='', pdfs_dir='', obj_classifier_model=None, author_classifier_model=None,
#                  load_obj_classifier_model=True, load_author_classifier_model=False, load_nlp=True):
#         super().__init__(pdfs_dir=pdfs_dir,obj_classifier_model=obj_classifier_model, author_classifier_model=author_classifier_model,
#                          load_obj_classifier_model=load_obj_classifier_model,
#                          load_author_classifier_model=load_author_classifier_model,
#                          load_nlp=load_nlp)
#         paps_load = self.load(all_papers_to_update_dir)
#         self.all_papers_old = paps_load['elements']
#         self.pdfs_files_names = list(self.all_papers_old.keys())
#
#
#
#     def add_paper(self,pdf_filename,save_dict=True,report=True):
#             pdf_path =self.all_papers_old[pdf_filename]['pdf_path']
#             new_paper = paper(path=pdf_path,
#                               obj_classifier_model=self.obj_classifier_model)
#             new_paper.database='mine'
#             # for abstract, take only the 200 first words
#             try:
#                 new_paper.Abstract =' '.join(self.all_papers_old[pdf_filename]['Abstract'].split()[:200])
#             except:
#                 new_paper.Abstract =' '.join(self.all_papers_old[pdf_filename]['Objective_paper'])
#             new_paper.Authors =self.all_papers_old[pdf_filename]['Authors']
#             new_paper.Publication_year = self.all_papers_old[pdf_filename]['Publication_year']
#             new_paper.Keywords = self.all_papers_old[pdf_filename]['Keywords']
#             # for conclusions, take only one with < 3000 words
#             if len(self.all_papers_old[pdf_filename]['Conclusion'].split()) <3000:
#                 new_paper.Conclusion = self.all_papers_old[pdf_filename]['Conclusion']
#             else:
#                 new_paper.Conclusion = ''
#             new_paper = replace_abbreviations(new_paper)
#             new_paper.get_objective_paper()
#             if report:
#                 new_paper.report_objectives()
#             if save_dict:
#                 self.elements[new_paper.file_name] = new_paper.save_paper_for_training()
#                 self.naimai_elements[new_paper.file_name] = new_paper.save_paper_for_naimai()
#             else:
#                 self.elements[new_paper.file_name] = new_paper
#
#     def get_papers(self,path_chunks='',save_dict=True, report=True):
#         idx=0
#         for pdf_filename in tqdm(self.pdfs_files_names):
#             try:
#                 self.add_paper(pdf_filename,save_dict=save_dict,report=report)
#             except:
#                 pass
#             if idx % 500 == 0 and path_chunks:
#                 print('  Saving idx {} for filename {}'.format(idx, pdf_filename))
#                 self.save(path_chunks)
#             idx += 1
#         print('Objs problem exported in objectives_pbs.txt')