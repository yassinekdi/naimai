<center>
  <img src="https://github.com/yassinekdi/naimai/logo.png?raw=true" alt="Naimai logo"/>
</center>

NaimAI is a Python package that structures each scientific paper using their abstract into 3 categories : objectives methods and results. 
Hence, when searching, the results will be showed by category. The results can also be reviewed and a review text will be 
automatically generated along with the references.
<br>
All the features are deployed on the <a href="https://www.naimai.fr" target="_blank">NaimAI's website</a>, where millions of paper are processed. 
<br>
A <a href="" target="_blank">Medium article</a> goes more in depth with naimai's features of the <a href="https://www.naimai.fr" target="_blank">web app</a>. 
<h1>Search in your own papers</h1>

You can either give a directory of folder with articles in PDF format or a csv file with abstracts and other meta data as showed 
<a href="tests/papers/input_data" target="_blank">here</a>.
<br>
The processing, the results and searching are explained in 
<a href="https://colab.research.google.com/drive/1xUDOkalxR7MFO6Zug48Cx1ysmgipaJCT?usp=sharing" target="_blank">this colab</a>.

<h1> Search in millions of papers </h1>
To search in the millions of papers already processed, you can use the <a href="https://www.naimai.fr" target="_blank">naimai website</a>.
I might open source this part too if needed.

<h1>Structure your abstract</h1>
If you already have an abstract and want to test the segmentor (naimai's algorithm that structures abstract into Background, 
Objectives, Methods and Results), <a href="https://colab.research.google.com/drive/16PMGC7yxkTcFpUnlZtioBMa22tpaTid5?usp=sharing">this colab</a>
walks you through the necessary steps.

<h1> Features to improve </h2>



<h1>References</h1>
<ul>
    <li>
    For abbreviations purposes, I used <a href="https://gist.github.com/ijmarshall/b3d1de6ccf4fb8b5ee53" target="_blank">this code</a>.
    </li>
    <li>
    For PDF processing, I used <a href="https://github.com/kermitt2/grobid" target="_blank">Grobid</a>.
    </li>
</ul>


[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg