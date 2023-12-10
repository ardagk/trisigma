import os

os.environ.setdefault('CONFIG_DIR', os.path.join(os.getcwd(), 'config'))
os.system('export PYTHONPYCACHEPREFIX="$HOME/.cache/pycache/"')

