import os
from setuptools import find_packages, setup

def package_files(package_dir):
	root_pkg_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'src', package_dir)
	print(root_pkg_dir)
	paths = []
	for root, _, filenames in os.walk(root_pkg_dir):
		for filename in filenames:
			if os.path.splitext(filename)[1] != '.py':
				paths.append(os.path.join('..', root, filename))
	return paths

dirs = ['slippi', 'meleeai']

EXTRA_FILES = []
for d in dirs:
	EXTRA_FILES += package_files(d)
print(EXTRA_FILES)
	
setup(
    author='Abszol',
    author_email='kdarling95@yahoo.com',
    name='meleeai',
    version='1.0.0',
    classifiers=(
        'Programming Language :: Python :: 3'
    ),
    description='Melee AI for slippi client.',
    packages=find_packages('src'),
	package_data={'src': EXTRA_FILES},
	package_dir={'': 'src'},
    install_requires=[
        'matplotlib>=3.2.1',
        'numpy>=1.18.2',
        'pillow>=7.1.2',
        'py-ubjson>=0.15.0',
        'PyYaml>=5.3.1',
        'termcolor>=1.1.0',
        'tk>=0.1.0'
    ],
    python_requires='~=3.6',
    url='',
    entry_points={
        'console_scripts':
            [
                'alfred = meleeai.alfred:main'
            ]
    }
)
