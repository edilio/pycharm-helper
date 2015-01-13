# pycharm-helper
Little code to include .env variables into django settings for debugging in Pycharm

In order to debug GEVENT add this line to /Applications/PyCharm.app/helpers/pydev/pydevd_constants.py (OSX)
SUPPORT_GEVENT = int(os.getenv('GEVENT_SUPPORT', '0'))

Add GEVENT_SUPPORT=1 to the environments 

Run this command if you want to add your .env settings to the environment of every config in PyCharm

./add_env.py <folder>

ex. ./add_env.py /Users/ediliogallardo/projects/newage/saas-load

It will ask for the name of django settings file. It will append .settings if not provided. 
