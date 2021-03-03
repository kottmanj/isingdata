import setuptools
import os

setuptools.setup(
    name="mystuff",
    version="4.20",
    author="Jakob S. Kottmann",
    author_email="jakob.kottmann@utoronto.ca",
    url="tba",
    packages=["isingdata"],
    package_dir={"": "src/python"},
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: Hopefully OS Independent",
    ),
    install_requires=["tequila-basic", "qulacs"],

)
