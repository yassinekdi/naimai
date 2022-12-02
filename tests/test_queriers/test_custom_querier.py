from unittest import TestCase
from naimai.papers.only_abstracts.issn import papers_issn
from naimai.pipelines.producers import Custom_Producer
from naimai.data_queriers.custom_querier import CustomQuerier
import os


class CustomQuerierTest(TestCase):
    """
    Test custom querier, by producing issn papers in test input data.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.review = """
        - Haruna and Nkongolo (2020) evaluated the influence of three years of cover crop, tillage, and crop rotation on selected soil nutrients.\n- Fontanazza et al. (2021) accelerated the degradation of biodegradable plastic (BP) mulch films and decreased the plastic pollution in agriculture.\n- Zarzecka et al. (2020) observed in plots where potato had been treated with herbicides and herbicides mixed with biostimulants ranging from 72.4 % to 96.1 % compared with the control.
        """
        cls.references = """
        - Samuel I. Haruna, N. Nkongolo, 2020, Influence of Cover Crop, Tillage, and Crop Rotation Management on Soil Nutrients, Agriculture.\n- Stefania Fontanazza, A. Restuccia, G. Mauromicale, A. Scavo, C. Abbate, 2021, Pseudomonas putida Isolation and Quantification by Real-Time PCR in Agricultural Soil Biodegradable Mulching, Agriculture.\n- K. Zarzecka, M. Gugała, A. Sikorska, K. Grzywacz, M. Niewęgło
        """

        cls.first_paper_result = {
            "website": "",
            "year": 2020,
            "database": "issn",
            "messages": [
                "Cover cropping, tillage and crop rotation management can influence soil nutrient availability and crop yield through changes in soil physical, chemical and biological processes.",
                "The objective of this study was to evaluate the influence of three years of cover crop, tillage, and crop rotation on selected soil nutrients.",
                "Twenty-four plots each of corn (Zea mays) and soybean (Glycine max) were established on a 4.05 ha field and arranged in a three-factor factorial design.",
                "The three factors (treatments) were two methods of tillage (no-tillage (NT) vs. moldboard plow [conventional] tillage (CT)), two types of cover crop (no cover crop (NC) vs. cover crop (CC)) and four typess of rotation (continuous corn, continuous soybean, corn/soybean and soybean/corn).",
            ],
            "reported": "Haruna and Nkongolo (2020) evaluated the influence of three years of cover crop, tillage, and crop rotation on selected soil nutrients.",
            "title": "Influence of Cover Crop, Tillage, and Crop Rotation Management on Soil Nutrients",
            "numCitedBy": 5.0,
            "journal": "Agriculture",
            "authors": "Haruna and Nkongolo (2020)",
            "allauthors": "Samuel I. Haruna, N. Nkongolo",
        }
        # reading data
        path = os.path.join("tests", "papers", "input_data", "issn_input.csv")
        obj = papers_issn(path, database="issn")
        obj.get_papers(update_dois=False, show_tqdm=False, check_database=False)

        # producing data
        producer = Custom_Producer(papers_dict=obj.elements)
        producer.produce_custom_papers(show_tqdm=False)

        # querying
        produced_papers = producer.produced_custom_papers
        cls.querier = CustomQuerier(produced_papers=produced_papers)
        cls.query = "cover crop"

        # reviewing
        cls.review_result, cls.references_result = cls.querier.review(cls.query)

    def test_papers_results(self):
        """
        test numcitedby of the first paper
        :return:
        """
        papers = self.querier.find_papers(self.query)
        first_paper = papers[0]
        self.assertEqual(type(papers),list)
        self.assertEqual(first_paper, self.first_paper_result)

    def test_review(self):
        """
        test if correct fnames are read
        :return:
        """
        self.assertEqual(self.review_result, self.review)

    def test_references(self):
        """
        test title of the first paper
        :return:
        """
        self.assertEqual(self.references_result[:400], self.references)
