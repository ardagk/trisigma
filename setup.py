from setuptools import setup, find_packages
import glob

packages = find_packages(exclude=['tests','cli', 'cli.*'])

setup(name='trisigma',
      version='1.0.0',
      description='Algo trading SDK',
      author='Arda Gok',
      author_email='ardagkmhs@gmail.com',
      packages=packages,
      package_dir={'tris_cli': 'cli/tris_cli'},
      include_package_data=True,
      scripts=glob.glob('scripts/*'),
     )

