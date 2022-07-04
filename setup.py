from setuptools import setup, find_packages


setup(
    name='robomania',
    version='0.0.1',
    packages=find_packages(where='robomania'),
    package_dir={'': 'src'},
    zip_safe=True,
)
