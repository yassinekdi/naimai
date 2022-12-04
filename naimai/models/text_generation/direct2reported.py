from spacy.symbols import VERB, dobj, nsubjpass, pobj, auxpass, xcomp, advcl, prep, ccomp
import re
import pyinflect
import spacy
from naimai.constants.nlp import past_tense, nlp_vocab,root_dep,conj_dep, nlp_disabled_direct2reported
from naimai.constants.regex import study_terms, regex_arxiv_filename
#from naimai.constants.paths import aws_root_pdfs
from naimai.constants.replacements import reported_corrections
from naimai.utils.regex import multiple_replace, reinsert_commas


class Direct2Reported:
    def __init__(self, authors, sentence, nlp=None):
        if nlp:
            self.nlp = nlp
            self.sentence = self.nlp(sentence)
        else:
            self.nlp = spacy.load(nlp_vocab)
            self.sentence = self.nlp(sentence, disable=nlp_disabled_direct2reported)
        self.dependencies = [nsubjpass, dobj, pobj, advcl, prep, ccomp]
        self.verb_dependencies = [root_dep, conj_dep]
        self.corrections_replacements = reported_corrections
        self.authors = authors
        self.action_verbs = []
        self.bows = {}
        self.reported = ''

    def tokenize(self):
        sentence_split = re.findall(r"[\w']+|[.,!?;]", self.sentence.text)
        return sentence_split

    def select_verb_in_2vbs(self, id_verb_to_remove, sentence_split):
        to_remove = id_verb_to_remove[0]
        if 'and' == sentence_split[to_remove - 1]:
            del sentence_split[to_remove - 1:to_remove + 1]
        return self.nlp(' '.join(sentence_split))

    def select_verb_in_3vbs(self, id_verb_to_remove, sentence_split):
        to_remove = id_verb_to_remove[0]
        if 'and' == sentence_split[to_remove - 1]:
            del sentence_split[to_remove - 4:to_remove + 1]
        return self.nlp(' '.join(sentence_split))

    def select_verbs(self):
        all_verbs = self.get_all_verbs(in_str=True)
        sentence_split = self.tokenize()
        verbs_idxs = [sentence_split.index(elt) for elt in all_verbs]

        try:
            if len(verbs_idxs) > 0:
                id_verb_to_remove_in_2vbs = [verbs_idxs[i + 1] for i in range(len(verbs_idxs) - 1) if
                                             verbs_idxs[i + 1] == verbs_idxs[
                                                 i] + 2]  # action_verb1, action verb2, and action_verb3 -> action_verb1
                id_verb_to_remove_in_3vbs = [verbs_idxs[i + 1] for i in range(len(verbs_idxs) - 1) if
                                             (verbs_idxs[i + 1] == verbs_idxs[i] + 3) and (verbs_idxs[i] == verbs_idxs[
                                                 i - 1] + 2)]  # action_verb1 and action verb1 -> action_verb1

                if id_verb_to_remove_in_2vbs:
                    self.sentence = self.select_verb_in_2vbs(id_verb_to_remove_in_2vbs, sentence_split)

                if id_verb_to_remove_in_3vbs:
                    self.sentence = self.select_verb_in_3vbs(id_verb_to_remove_in_3vbs, sentence_split)

        except:
            pass

    def get_all_verbs(self, in_str=False):
        result = []
        if in_str:
            result = [token.text for token in self.sentence if token.pos == VERB]
        else:
            result = [token for token in self.sentence if token.pos == VERB]
        return result

    def get_bow_of_verb(self, verb):
        right_words = self.get_words_verb(verb)
        right_words_children = []
        # get the bow in the right dependency direction
        if right_words:
            for wd in right_words:
                right_words_children += [child for child in wd.subtree]
            return right_words_children
        # else:
        #     print('No next word after verb in ', self.sentence)

    def correct_bow(self):
        # in case words of second verb were considered in the first verb two, they're removed
        first_verb = self.action_verbs[0]
        if len(self.bows) == 2:
            second_verb = self.action_verbs[1]
            self.bows[first_verb] = [elt for elt in self.bows[first_verb] if elt not in self.bows[second_verb]]
            try:
                self.bows[first_verb].remove(second_verb)
            except:
                pass

    def get_bow(self):
        self.select_verbs()
        self.get_action_verbs()

        if self.action_verbs:
            # get right direction using dependencies
            for verb in self.action_verbs:
                self.bows[verb] = self.get_bow_of_verb(verb)

            self.correct_bow()
        # else:
        #     print('No action verbs in ', self.sentence)

    def sort_bows(self):
        for verb in self.bows:
            positions = sorted(self.bows[verb], key=lambda word: word.idx)
            self.bows[verb] = [word for word in positions]

    def is_passive(self):
        verbs = [token for token in self.sentence if token.dep == auxpass]
        if verbs:
            return True
        return False

    def get_action_verbs(self):
        all_verbs = self.get_all_verbs()
        verbs_xcomp = [token for token in all_verbs if (token.dep == xcomp) or (token.dep_ in self.verb_dependencies)]
        self.action_verbs = verbs_xcomp

    def get_words_verb(self, verb):
        return [token for token in verb.children if token.dep in self.dependencies]

    def final_corrections(self):
        correct_characters = multiple_replace(self.corrections_replacements, self.reported)
        correct_thispaper = re.sub(
            '(?:in)? (?:this|their|the|our) (?:present|experimental|numerical)?\s?(?:' + study_terms + ')', '',
            correct_characters, flags=re.I)
        correct_space = re.sub('\s+', ' ', correct_thispaper)
        self.reported = correct_space.replace('and to and', 'and')
        self.reported = reinsert_commas(self.sentence.text, self.reported)

    def add_adverb(self):
        res = ''
        experiment = re.findall('experiment|laboratory', self.sentence.text)
        if experiment:
            res += 'experimentally'

        numeric = re.findall('simulat|numeric', self.sentence.text)
        if numeric:
            if experiment:
                res += ' and numerically'
            else:
                res += 'numerically'
        return res

    def initial_corrections(self):
        sentence = self.sentence.text
        correct_sentence0 = re.sub('(?:\(\d+\)|\[\d+\])', '', sentence)
        correct_sentence = re.sub('(?:\(i+\)|\[i+\])', '', correct_sentence0)
        correct_dir_verbs = re.sub('(?:focus(?:es)? on |(?:to)? understand |deals? with )', 'study ', correct_sentence)
        correct_dir_verbs2 = re.sub('carr(?:y|ied) out ', 'analyzed ', correct_dir_verbs)
        correct_dir_verbs3 = re.sub('aim(?:s|ed)? (?:to|at) ', ' ', correct_dir_verbs2)
        self.sentence = self.nlp(correct_dir_verbs3)

    def generate_for_1_dir_verb(self, verb, try_adverbs=False):
        next_words = [word.text for word in self.bows[verb]]
        adverbs = ''
        if self.is_passive():
            next_words[0] = next_words[0].lower()
        verb_past = verb._.inflect(past_tense)

        if try_adverbs:
            if ('experiment' not in next_words) or ('numeric' not in next_words):
                adverbs = self.add_adverb()

        final = [verb_past] + [adverbs] + next_words
        return final

    def generate(self,review_nb=1,uploaded=False):
        # first corrections
        self.initial_corrections()

        # get bow in the right dependency direction
        self.get_bow()
        self.sort_bows()

        # gather everything
        final = []
        for verb in self.bows:
            final.append(self.generate_for_1_dir_verb(verb))

        for elt in final[1:]:
            elt.insert(0, 'and')
        obj = [elt for bow in final for elt in bow]
        if obj:
            if uploaded:
                link="<b>{}</b><sup>{}</sup>".format(self.authors, review_nb+1)
            else:

                link = self.authors
            # link=self.authors
            final_flatten = [link] + obj
            self.reported = ' '.join(final_flatten) + '.'
            self.final_corrections()

