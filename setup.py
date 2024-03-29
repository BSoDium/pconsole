from setuptools import setup
from pconsole.version import __version__ as v  

with open('README.md') as d:
    desc = d.read()

setup(name = 'pconsole',
      author = 'l3alr0g',
      version = v,
      url = 'https://github.com/l3alr0g/pconsole',
      license = 'MIT',
      packages = ['pconsole'],
      zip_safe = True,
      python_requires='>=3.5',
      description = 'Console for panda3d application written in python',
      long_description = desc,
      long_description_content_type = 'text/markdown',
      include_package_data = True,
      platforms=['Windows', 'Linux', 'OSX'],
      install_requires = [
        'panda3d',
        'importlib',
        'pathlib',
        'requests',
      ]
)
