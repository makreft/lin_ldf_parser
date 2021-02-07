from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="lin_parser",
    version="0.01",
    description="Simple regex based parser for the lin description file.",
    py_modules="lin_parser",
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy ~= 1.20.0",
        "pandas ~= 1.2.1",
        "pip ~= 21.0.1",
    ],
    extras_require={
        "dev": [
            "pytest >= 6.2.2",
        ]
    },
    url="https://github.com/makreft/ldf_parser",
    author="Marco Kreft",
)
