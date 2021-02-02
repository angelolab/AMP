from sys import version
import setuptools

with open("readme.md", 'r', encoding='utf-8') as fh:
    long_description = fh.read()

dependencies = [
    'matplotlib==3.3.2',
    'numpy>=1.19.2',
    'pillow==8.1.0',
    'PyQt5==5.9.2',
    'scipy>=1.5.2',
]

setuptools.setup(
    name="amp",
    version="0.1.0-alpha",
    author="Angelo Lab",
    author_email="ackagel@stanford.edu",
    description="Base AMP importable modules",
    long_description=long_description,
    long_description_content_type = 'text/markdown',
    url="https://github.com/angelolab/AMP",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    install_requires=dependencies,
    python_requires='==3.6.*'
)
