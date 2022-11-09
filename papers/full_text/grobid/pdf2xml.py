'''
Modified grobid client from Grobid source: https://github.com/kermitt2/grobid. The GrobidClient object
takes a directory of PDFs and converts it to XML files as explained in the process method.
'''
import os
import json
import time
import concurrent.futures
import requests
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup
import shutil

from .client import ApiClient


class ServerUnavailableException(Exception):
    pass


class GrobidClient(ApiClient):

    def __init__(self, url,
                 coordinates=["persName", "figure", "ref", "biblStruct", "formula", "s"],
                 sleep_time=5,
                 timeout=180,
                 config_path=None,
                 check_server=True):
        self.config = {
            'url': url,
            'coordinates': coordinates,
            'sleep_time': sleep_time,
            'timeout': timeout
        }
        if config_path:
            self._load_config(config_path)
        if check_server:
            self._test_server_connection()

    def _load_config(self, path="./config.json"):
        """
        Load the json configuration
        """
        config_json = open(path).read()
        self.config = json.loads(config_json)

    def _test_server_connection(self):
        """Test if the server is up and running."""
        the_url = self.config['url']
        r = requests.get(the_url)

        status = r.status_code

        if status != 200:
            print("GROBID server does not appear up and running " + str(status))
        else:
            print("GROBID server is up and running")

    def process(
            self,
            service,
            input_path: str,
            n=10,
            generateIDs=False,
            consolidate_header=True,
            consolidate_citations=False,
            include_raw_citations=False,
            include_raw_affiliations=False,
            tei_coordinates=False,
            segment_sentences=False,
            verbose=False,
            path_export='',
            path_export_new_fnames_pdfs='',
            idx_start=0,
            idx_finish=-1
    ):
        '''
        Process a path of PDFs (input_path) and converts the files into XML files exported in
        path_export.

        :param input_path: of PDF files
        :param path_export: where the PDF files are exported in XML format
        :param path_export_new_fnames_pdfs: where the XML files are exported with title as filename
        :param idx_start: can process all the files in input_path starting from idx_start^th file
        :param idx_finish: can process all the files in input_path until the idx_start^th file
        :return:
        '''

        input_files = []
        result = {}
        if idx_finish==-1:
            filenames = sorted(os.listdir(input_path))[idx_start:]
        else:
            filenames = sorted(os.listdir(input_path))[idx_start:idx_finish]

        for filename in tqdm(filenames):
            if filename.endswith(".pdf") or filename.endswith(".PDF") or \
                    (service == 'processCitationList' and (filename.endswith(".txt") or filename.endswith(".TXT"))):
                if verbose:
                    try:
                        print(filename)
                    except Exception:

                        pass
                input_files.append(os.sep.join([input_path, filename]))

                result[filename] = self.process_batch(
                    service,
                    input_files,
                    n,
                    generateIDs,
                    consolidate_header,
                    consolidate_citations,
                    include_raw_citations,
                    include_raw_affiliations,
                    tei_coordinates,
                    segment_sentences,
                    verbose,
                )
                input_files = []

        if path_export:
            print('Files exported in :', path_export)
            for fname in result:
                text = result[fname]
                title = self.get_paper_title(text)
                if title:
                    title = title.replace('/','_')
                    fle_name = title+'.xml'
                    new_pdf_name = title+'.pdf'
                    output_pdf_path = os.path.join(path_export_new_fnames_pdfs, new_pdf_name)
                    intput_pdf_dir = os.path.join(input_path,fname)
                    shutil.copyfile(intput_pdf_dir, output_pdf_path)
                else:
                    fle_name = fname.replace('pdf','xml')
                output_fname = os.path.join(path_export,fle_name)


                with open(output_fname,'w',encoding='utf8') as xml_file:
                    xml_file.write(text)

        return result

    def get_paper_title(self,text):
        name = 'title'
        attrs = {'type': 'main'}

        soup = BeautifulSoup(text, "lxml")
        content = soup.find(name=name, attrs=attrs)
        if content:
            return content.text
        return
    def process_batch(
            self,
            service,
            input_files,
            n,
            generateIDs,
            consolidate_header,
            consolidate_citations,
            include_raw_citations,
            include_raw_affiliations,
            tei_coordinates,
            segment_sentences,
            verbose=False,
    ):
        if verbose:
            print(len(input_files), "files to process in current batch")

        # we use ThreadPoolExecutor and not ProcessPoolExecutor because it is an I/O intensive process
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
            # with concurrent.futures.ProcessPoolExecutor(max_workers=n) as executor:
            results = []
            for input_file in input_files:
                selected_process = self.process_pdf
                if service == 'processCitationList':
                    selected_process = self.process_txt

                r = executor.submit(
                    selected_process,
                    service,
                    input_file,
                    generateIDs,
                    consolidate_header,
                    consolidate_citations,
                    include_raw_citations,
                    include_raw_affiliations,
                    tei_coordinates,
                    segment_sentences)

                results.append(r)
        for r in concurrent.futures.as_completed(results):
            input_file, status, text = r.result()
            # filename = self._output_file_name(input_file, input_path, output)

            if text is None:
                print("Processing of", input_file, "failed with error", str(status))
                return ''
            else:
                return text

    def process_pdf(
            self,
            service,
            pdf_file,
            generateIDs,
            consolidate_header,
            consolidate_citations,
            include_raw_citations,
            include_raw_affiliations,
            tei_coordinates,
            segment_sentences
    ):
        if isinstance(pdf_file,bytes):
            files = {
                "input": (
                    pdf_file,
                    pdf_file,
                    "application/pdf",
                    {"Expires": "0"},
                )
            }
        else:
            files = {
                "input": (
                    pdf_file,
                    open(pdf_file, "rb"),
                    "application/pdf",
                    {"Expires": "0"},
                )
            }
        the_url = self.config['url']
        the_url += "/api/" + service

        # set the GROBID parameters
        the_data = {}
        if generateIDs:
            the_data["generateIDs"] = "1"
        if consolidate_header:
            the_data["consolidateHeader"] = "1"
        if consolidate_citations:
            the_data["consolidateCitations"] = "1"
        if include_raw_citations:
            the_data["includeRawCitations"] = "1"
        if include_raw_affiliations:
            the_data["includeRawAffiliations"] = "1"
        if tei_coordinates:
            the_data["teiCoordinates"] = self.config["coordinates"]
        if segment_sentences:
            the_data["segmentSentences"] = "1"

        try:

            res, status = self.post(
                url=the_url, files=files, data=the_data, headers={"Accept": "text/plain"},
                timeout=self.config['timeout']
            )

            if status == 503:
                time.sleep(self.config["sleep_time"])
                return self.process_pdf(
                    service,
                    pdf_file,
                    generateIDs,
                    consolidate_header,
                    consolidate_citations,
                    include_raw_citations,
                    include_raw_affiliations,
                    tei_coordinates,
                    segment_sentences
                )
        except requests.exceptions.ReadTimeout:
            return (pdf_file, 408, None)

        return (pdf_file, status, res.text)

    def process_txt(
            self,
            service,
            txt_file,
            generateIDs,
            consolidate_header,
            consolidate_citations,
            include_raw_citations,
            include_raw_affiliations,
            tei_coordinates,
            segment_sentences
    ):
        # create request based on file content
        references = None
        with open(txt_file) as f:
            references = [line.rstrip() for line in f]

        the_url = self.config['url']
        the_url += "/api/" + service

        # set the GROBID parameters
        the_data = {}
        if consolidate_citations:
            the_data["consolidateCitations"] = "1"
        if include_raw_citations:
            the_data["includeRawCitations"] = "1"
        the_data["citations"] = references
        res, status = self.post(
            url=the_url, data=the_data, headers={"Accept": "application/xml"}
        )

        if status == 503:
            time.sleep(self.config["sleep_time"])
            return self.process_txt(
                service,
                txt_file,
                generateIDs,
                consolidate_header,
                consolidate_citations,
                include_raw_citations,
                include_raw_affiliations,
                tei_coordinates,
                segment_sentences
            )

        return (txt_file, status, res.text)

