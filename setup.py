"""Setup script for the SEM SVG Gate Coloring Tool."""
from setuptools import find_packages, setup

setup(
    name='sem-colorer',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'matplotlib',
        'beautifulsoup4',
        'lxml',  # for xml parsing with beautifulsoup
    ],
    entry_points={
        'console_scripts': [
            'sem-colorer=sem_colorer.cli:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='SEM SVG Gate Coloring Tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/sem-colorer',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',  # for type hints used in the code
)