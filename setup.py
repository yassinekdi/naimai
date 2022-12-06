from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


setup(
    name = 'naimai',
    version = '1.0.0.2',
    author=  'Yassine Kaddi',
    author_email = 'yassine@naimai.fr',
    description = 'Python library to help with scientific literature research',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    maintainer = "Yassine Kaddi",
    maintainer_email = "yassine@naimai.fr",
    license = "CC BY-NC-SA",
    keywords = ['science', 'review','bibliography','python','nlp','machine-learning','information-extraction'],
    url =" https://github.com/yassinekdi/naimai",
    classifiers =[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent"
    ],
    packages = find_packages()
)
