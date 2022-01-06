regex_email = r'\w+@\w+\.\w+'
regex_url = r'http([^\s]+)'
regex_words=r'[^a-zA-Z+]'
regex_words_authors=r'[^a-zA-Z+\.,\-;]'
regex_words_commas=r'[^a-zA-Z(,|.) ]'
regex_not_converted = r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]'
regex_abstract1 = r'a\s*b\s*s\s*t\s*r\s*a\s*c\s*t'
regex_abstract2 = r's\s*u\s*m\s*m\s*a\s*r\s*y'
regex_year = '[12][0-9]{3}a?b?c?'
regex_sentences = r'\.(?=\s+[A-Z])'
regex_words_numbers_some=r'[^A-Za-z0-9\s\(\)\.,;\-]'
regex_etal_and = 'et\s+al\.,?\s+|and'
regex_etal_and_plus=regex_etal_and+'|\(|\)'
regex_remove_nbs_from_end = '[^0-9]+$'
regex_capital=r'\b(?=[A-Z])'
regex_cid = r'\(?cid:\d+\)?'
regex_arxiv_filename = '\d{4}\.\d+\.pdf'
arxiv_pdfs_url = 'https://arxiv.org/pdf/'
regex_words_in_brackets = '\((\w.+?)\)'

study_terms = 'paper|study|investigation|work|research'
verbs_terms =  'discuss(?:ed)?|evaluated?|used?|explored?|describe|developed?|introduced?|present(?:ed)?|investigated?|examined?|show(?:ed)?'
objective_terms = ' objectives? | purposes? | goals? | propose | aims | examines? | investigate '
rgx1 = '[^.]*(?:this|our|present) (?:'+study_terms+')[^.]*\.'
rgx2 = '[^.]*(?:we|authors|is|were|are|have|has|was) (?:' +verbs_terms +')[^.]*\.'
rgx3 = '[^.]* (?:' + objective_terms+')[^.]*\.?'
rgx4 = '[^.]* here[^.]*\.'
rgx5 = '[^.]*to this end[^.]*\.'
rgx6 = '[^.]*the present[^.]*\.'
rgx_or = '|'
regex_objectives = rgx1 + rgx_or + rgx2 + rgx_or + rgx3 + rgx_or + rgx4 + rgx_or + rgx5 + rgx_or + rgx6


# regex_doi = r'\b.*?doi.*'
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
regex_paper_year = ' 19[0-9]{2}|20[01][0-9]|202[01] '

regex_filtered_words_obj = 'this section|Corresponding| PhD '
