from setuptools import find_packages, setup

setup(
    name='robomania',
    version='0.3.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=True,
    package_data={'robomania': ['locale/*.json']},
)
