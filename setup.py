from setuptools import setup


setup(
    name='assistparser',
    description='Library for scraping ASSIST.org',
    version='1.0.0',
    author='Karina Antonio',
    author_email='karinafantonio@gmail.com',
    url='https://github.com/karinassuni/assistscraper',
    license='MIT',
    py_modules=['assistparser'],
    install_requires=[
        'regex',
    ],
)
