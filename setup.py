from setuptools import setup

version = '0.1.0'
name = 'arm'
install_requires = []

setup(name=name,
      version=version,
      description='Association rule mining',
      install_requires=install_requires,
      long_description=open('README.rst', 'rt').read(),
      author='Priyam Singh',
      author_email='priyamsingh.22296@gmail.com',
      packages=['arm'],
)
