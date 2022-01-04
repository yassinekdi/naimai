from paper2.constants.nlp import root_dep,verb_pos
from paper2.utils import find_root_verb
from spacy.symbols import VERB, nsubjpass
import re


class active_tense_processor:
    def __init__(self, sentence, nlp):
        self.nlp = nlp
        self.sentence = nlp(sentence)
        self.separators = []
        self.threshold = .7
        self.root_verb = None
        self.root_clause = None
        self.naive_clauses = []

    def get_separators(self):
        result = []
        tokens_to_split = ['which', 'and', 'but', "because", "while", "then", "also", ',', "that"]
        for token in self.sentence:
            if token.text in tokens_to_split:
                result.append(token)
        self.separators = result

    def naive_separator_segmentation(self):
        puncts = [',']
        self.get_separators()
        if self.separators:
            separators_text = [elt.text for elt in list(set(self.separators))]
            separators_uniques = [' ' + elt + ' ' if elt not in puncts else elt for elt in separators_text]
            separators_regex = '|'.join(separators_uniques)
            return re.split(separators_regex, self.sentence.text)
        return [self.sentence.text]

    def is_root_in_clause(self, clause_nlp):
        for token in clause_nlp:
            if token.text == self.root_verb.text:
                return True
        return False

    def idx_clause_with_root(self, first_clauses_list_nlp):
        first_idx = 0
        for clause in first_clauses_list_nlp:
            if self.is_root_in_clause(clause):
                first_idx = first_clauses_list_nlp.index(clause)
                break
        return first_idx

    def get_clauses(self):
        # segment to naive clauses
        naive_clauses = self.naive_separator_segmentation()
        separators = [''] + [token.text for token in self.separators]
        naive_clauses = [self.nlp(sep + ' ' + clause) for sep, clause in zip(separators, naive_clauses)]

        # remove clauses without root verb
        idx_clause_root = self.idx_clause_with_root(naive_clauses)
        self.root_clause = naive_clauses[idx_clause_root]

        # filter clauses with "that + verb"
        for clause in naive_clauses:
            if (clause.text != self.root_clause.text) and (clause[0].text == 'that') and (clause[1].pos == VERB):
                pass
            else:
                self.naive_clauses.append(clause)

    def transform_root_clause(self):
        idx_root_verb = [token.i for token in self.root_clause if token.text == self.root_verb.text][0]
        sub_clause = self.root_clause[idx_root_verb + 1:].text
        # conjugate root verb
        if self.root_verb.tag_ == 'VBZ' or self.root_verb.tag_ == 'VBN':
            root = self.root_verb._.inflect('VBP')
        else:
            root = self.root_verb.text
        new_sentence = 'we ' + root + ' ' + sub_clause
        return self.nlp(new_sentence)

    def transform_active_tense(self):
        first_clause_transformed = self.transform_root_clause()
        # restitution
        return [first_clause_transformed.text] + [clause.text for clause in self.naive_clauses if
                                                  clause.text != self.root_clause.text]

    def process(self):
        # find root verb
        self.root_verb = find_root_verb(sentence=self.sentence)

        # get root & naive clauses
        self.get_clauses()

        result = self.transform_active_tense()

        return ' '.join(result)


class clauses_processor:
  def __init__(self,sentence,nlp):
    self.nlp = nlp
    self.sentence = nlp(sentence)
    self.root_verb=None

  def is_root_passive(self):
    if self.root_verb.tag_=='VBN':
      if 'is' in [child.text for child in self.root_verb.children]:
        return True
    return False

  def find_subject_and_children(self):
    root_verb_subject= [token for token in self.root_verb.children if token.dep==nsubjpass][0]
    subject_children=list(root_verb_subject.subtree)
    subject_children_txt = [token.text for token in subject_children]

    idx_root_verb = [token.i for token in self.sentence if token.text == self.root_verb.text][0]
    rest_after_root_verb = self.sentence[idx_root_verb+1:]
    text_in_beginning = [token for token in list(self.root_verb.subtree) if (token.text not in subject_children_txt) and (token.text not in rest_after_root_verb.text)]

    # remove original root verb:
    for idx,token in enumerate(text_in_beginning):
      if token.text ==self.root_verb.text:
        try:
          del text_in_beginning[idx-1] #delete is
          del text_in_beginning[idx-1] #delete original verb
          break
        except:
          pass
    root_verb_children=subject_children+ [rest_after_root_verb] + text_in_beginning
    root_verb_children =[token.text for token in root_verb_children]
    return root_verb_children

  def passive2active(self):
    rest_of_sentence = self.find_subject_and_children()
    rest_of_sentence = ' '.join(rest_of_sentence)
    root_verb_present_tense = self.root_verb._.inflect('VBP')
    new_sentence = 'we '+ root_verb_present_tense + ' ' + rest_of_sentence
    return new_sentence

  def process_active_tense(self,sentence,nlp):
    processor = active_tense_processor(sentence=sentence, nlp=nlp)
    return processor.process()

  def process(self):
    # find root verb
    self.root_verb = find_root_verb(sentence=self.sentence)

    # if root is active tense format :
    if not self.is_root_passive():
      new_sentence = self.process_active_tense(sentence=self.sentence.text,
                                               nlp = self.nlp)

    else: # if root is passive tense format :
      active_tense = self.passive2active()
      new_sentence = self.process_active_tense(sentence=active_tense,
                                               nlp = self.nlp)
    return new_sentence


class objective_sentence_processor:
    def __init__(self, sentence, nlp):
        self.nlp = nlp
        self.raw_sentence = nlp(sentence)
        self.processed_sentence = None
        self.final_sentence = ''
        self.clauses_processor = None

    # deal with 2 successive verbs & replace beginning with we
    def get_second_verb_when_2_sucessive_verbs(self):
        for token in self.processed_sentence:
            if token.pos_ == verb_pos and token.dep_ == root_dep and token.text != 'used':
                try:
                    next_token = self.processed_sentence[token.i + 1]
                    if next_token.pos_ == 'PART':
                        next_next_token = self.processed_sentence[token.i + 2]
                        if next_next_token.pos_ == verb_pos:
                            return next_next_token
                except:
                    pass
        return

    def fix_2_successive_verbs(self):
        second_verb = self.get_second_verb_when_2_sucessive_verbs()
        if second_verb:
            second_verb_idx = [token.i for token in self.processed_sentence if token == second_verb][0]
            sub_sentence = self.processed_sentence[second_verb_idx + 1:]

            second_verb_text = second_verb.text
            if 'understand' in second_verb_text:
                second_verb_text = 'analyze'

            new_sentence = 'we ' + second_verb_text + ' ' + sub_sentence.text
            self.processed_sentence = self.nlp(new_sentence)

    def get_table_infos(self, processed=True):
        if processed:
            sentence = self.processed_sentence
        else:
            sentence = self.raw_sentence
        print('Token\tIndex\tPOS\tTag\tDep\tAncestor\tChildren')
        for token in sentence:
            ancestors = [t.text for t in token.ancestors]
            children = [t.text for t in token.children]
            print(token.text[:6], "\t", token.i, "\t",
                  token.pos_, "\t",
                  token.tag_, "\t", token.dep_, "\t",
                  ancestors, "\t", children)

    def remove_some_words(self):
        doc_text = re.sub('in particular,?|moreover,?|furthermore,?| also|', '', self.raw_sentence.text, flags=re.I)
        self.processed_sentence = self.nlp(doc_text)

    def replace_synonyms(self):
        pattern = 'together with|along with|as well as|in addition to|besides'
        self.processed_sentence = self.nlp(re.sub(pattern, 'and', self.processed_sentence.text))

    def remove_which_clauses(self):
        # pattern= '[^by which],?\s?(which|through|as\s?a? part of).*?,'
        pattern = '(by which.*)|(,?\s?(which|through|as\s?a? part of).*?,)'
        self.processed_sentence = self.nlp(re.sub(pattern, '', self.processed_sentence.text))

    def remove_numerotations(self):
        doc_text = re.sub(' \((i+v?)\)|\((\d)\)|\(v\)', '', self.processed_sentence.text)
        self.processed_sentence = self.nlp(doc_text)

    def clause_has_verb_or_subject(self, clause):
        root_verb = find_root_verb(sentence=self.processed_sentence)

        subject = [token for token in root_verb.children if token.dep == nsubjpass]
        if subject:
            subject = subject[0].text
        else:
            subject = 'ZZZ'
        for token in clause:
            if (token.pos == VERB) or (token.text == subject):
                return True
        return False

    def remove_first_clause_without_verb(self):
        clauses_by_comma_separator = self.processed_sentence.text.split(',')
        first_clause = self.nlp(clauses_by_comma_separator[0])
        if not self.clause_has_verb_or_subject(first_clause):
            self.processed_sentence = self.nlp(' '.join(clauses_by_comma_separator[1:]))

    def process(self):
        # first processings
        self.remove_some_words()
        # print('some words removed : ', self.processed_sentence)
        self.remove_first_clause_without_verb()
        # print('without first clause removed : ', self.processed_sentence)
        self.remove_which_clauses()
        # print('without which clause removed : ', self.processed_sentence)
        self.remove_numerotations()
        self.replace_synonyms()

        # fix 2 successive verbs
        self.fix_2_successive_verbs()

        # process
        self.clauses_processor = clauses_processor(sentence=self.processed_sentence.text, nlp=self.nlp)
        self.final_sentence = self.clauses_processor.process()