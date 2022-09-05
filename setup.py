from setuptools import find_packages, setup

setup(
    name='robomania',
    version='0.0.2',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=True,
)
