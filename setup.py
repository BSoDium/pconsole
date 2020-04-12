from setuptools import setup


with open('README.md') as d:
    desc = d.read()

setup(name = 'pconsole',
      author = 'l3alr0g',
      version = '0.1',
      url = 'https://github.com/l3alr0g/pconsole',
      license = 'None',
      packages = ['pconsole'],
      zip_safe = False,
      description = 'Console for panda3d application written in python',
      long_description = desc
)