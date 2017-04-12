from setuptools import setup

version = '0.1.0'
name = 'arm'
install_requires = ['beautifultable']

setup(name=name,
      version=version,
      description='Association rule mining',
      install_requires=install_requires,
      long_description=open('README.rst', 'rt').read(),
      author='Priyam Singh',
      author_email='priyamsingh.22296@gmail.com',
      packages=['arm'],
      url='https://github.com/pri22296/{0}'.format(name),
      download_url='https://github.com/pri22296/{0}/tarball/{1}'.format(name, version),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.5',
      ],
)
