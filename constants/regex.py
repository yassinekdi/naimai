regex_email = r'\w+@\w+\.\w+'
regex_url = r'http([^\s]+)'
regex_words=r'[^a-zA-Z+]'
regex_words_authors=r'[^a-zA-Z+\.,\-;]'
regex_words_commas=r'[^a-zA-Z(,|.) ]'
regex_not_converted = r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]'
regex_not_converted2 = '\\u2009|\\xa0'
regex_abstract1 = r'a\s*b\s*s\s*t\s*r\s*a\s*c\s*t'
regex_abstract2 = r's\s*u\s*m\s*m\s*a\s*r\s*y'
regex_year = '[12][0-9]{3}a?b?c?'
regex_sentences = r'\.(?=\s+[A-Z])'
regex_words_numbers_some=r'[^A-Za-z0-9\s\(\)\.,;\-]'
regex_etal = 'et\s+al\.\s?'
regex_etal_and = 'et\s+al\.,?\s+|and'
regex_etal_and_plus=regex_etal_and+'|\(|\)'
regex_remove_nbs_from_end = '[^0-9]+$'
regex_capital=r'\b(?=[A-Z])'
regex_cid = r'\(?cid:\d+\)?'
regex_arxiv_filename = '\d{4}\.\d+\.pdf'
arxiv_pdfs_url = 'https://arxiv.org/pdf/'
regex_words_in_brackets = '\((\w.+?)\)'
regex_in_brackets='\((.*?)\)'

study_terms = 'paper|study|investigation|work|research'
verbs_terms =  'hypothesize|aim(?:ed)?|proposed?|remedy|discuss(?:ed)?|evaluated?|used?|explored?|describes?|developed?|introduced?|present(?:ed)?|investigated?|examined?|show(?:ed)?'
objective_terms = ' objectives? | purposes? | goals? | propose | aims | examines? | investigate '
rgx1 = '[^.]*(?:this|our|present) (?:'+study_terms+')[^.]*\.'
rgx2 = '[^.]*(?:we|authors|is|were|are|have|has|was) (?:' +verbs_terms +')[^.]*\.'
rgx3 = '[^.]* (?:' + objective_terms+')[^.]*\.?'
rgx4 = '[^.]* here[^.]*\.'
rgx5 = '[^.]*to this end[^.]*\.'
rgx6 = '[^.]*the present[^.]*\.'
rgx7 = '(?:to \w+ this, )(?:.*?)\.'
rgx_or = '|'
regex_objectives = rgx1 + rgx_or + rgx2 + rgx_or + rgx3 + rgx_or + rgx4 + rgx_or + rgx5 + rgx_or + rgx6 + rgx_or + rgx7

regex_spaced_chars = '(.) (.)'
regex_abbrvs = 'i\.e\.?,?|e\.g\.?,?'
regex_abbrvs2 = 'cf\.'
regex_some_brackets = r'\((figure|table|meaning).*?\)'
regex_numbers_in_brackets = r'(\(|\[)\d\d?(\)|\])\s?'
regex_eft = r'(\(|\[)?(figure|fig\.|table|equation|eqs?\.)(\)|\])?'
regex_explained_2pts = '(:\s?.*?)\.'
regex_equation_tochange=r'(\w+)\s?=\s?(\w+(?:\.\w+))'
regex_equation='\w+\s?=\s?\w+(?:\.\w+)?'
regex_keywords='key\s?words:(.*)'
regex_background = 'introduction|background'
regex_objective = 'purpose|aim|objective'
regex_methods = 'method|materials|approach'
regex_results = 'result|finding|conclusion'
regex_doi = r"""
    ((\(?doi(\s)*\)?:?(\s)*)       # 'doi:' or 'doi' or '(doi)' (upper or lower case)
    |(https?://(dx\.)?doi\.org\/))?         # or 'http://(dx.)doi.org/'  (neither has to be present)
    (?P<doi>10\.                            # 10.                        (mandatory for DOI's)
    \d{3,7}                                 # [0-9] x 3-7
    (\.\w+)*                                # subdivisions separated by . (doesn't have to be present)
    (/|%2f)                                 # / (possibly urlencoded)
    [\w\-_:;\(\)/\.<>]+                     # any character
    [\w\-_:;\(\)/<>])                       # any character excluding a full stop
    """
regex_references = r'references(.*)\b'
regex_urlsoup=r'q=(.*)&sa=U&ved'
regex_paper_year = '19[0-9]{2}|20[01][0-9]|202[0-2]'

regex_filtered_words_obj = 'this section|Corresponding| PhD '
regex_remove_from_ssrn_fields = '&\s?|eJournal|Educator:?|Courses, Cases & Teaching|Teaching'
regex_journal_names = '[^A-Za-z\s]'
regex_journal_names2 = 'volume|issue|\n|doi'

regex_abstract_omr = 'objectives?:|results?:|questions?:|purposes?:|findings:|methods:|conclusion:|report:|discussions?:'
regex_review = 'review|summarizes?|document'