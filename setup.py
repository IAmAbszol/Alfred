import os
from setuptools import find_packages, setup
from typing import Iterator

def package_files(package_dir: str) -> Iterator[str]:
    """Gathers a list of non-.py file paths in the given package directory.
    :param package_dir: Name of directory within this package to search.
    :return: Iterator of file paths.
    """
    root_pkg_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'meleeai', package_dir)
    for root, _, file_names in os.walk(root_pkg_dir):
        for file_name in file_names:
            if os.path.splitext(file_name)[1] not in ('.py', '.pyc'):
                yield os.path.join('..', root, file_name)


EXTRA_FILES = [*package_files('.')]
print(f'Found paths: {EXTRA_FILES}')

setup(
    author='Abszol',
    author_email='kdarling95@yahoo.com',
    name='meleeai',
    version='0.1.0',
    classifiers=(
        'Programming Language :: Python :: 3'
    ),
    description='Melee AI for slippi client.',
    packages=find_packages(),
	package_data={'': EXTRA_FILES},
	package_dir={'': '.'},
    install_requires=[
        'absl-py>=0.11.0',
        'importlib-metadata>=2.0.0',
        'gym>=0.17.3',
        'matplotlib>=3.2.1',
        'numpy>=1.18.2',
        'pillow>=7.1.2',
        'pykalman==0.9.5',
        'py-ubjson>=0.15.0',
        'scipy>=1.5.1',
        'Sphinx==3.1.2',
        'termcolor>=1.1.0',
        'tk>=0.1.0'
    ],
    python_requires='>=3.6, <3.10',
    url='',
    entry_points={
        'console_scripts':
            [
                'alfred = meleeai.alfred:main'
            ]
    }
)
