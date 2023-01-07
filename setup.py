from setuptools import find_packages, setup

setup(
    name='robomania',
    version='0.4.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=True,
    package_data={'robomania': ['locale/*.json']},
)
