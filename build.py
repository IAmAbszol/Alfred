"""
    Makes building Alfred easy
"""

import os
import platform
import struct
import subprocess
import sys

def subprocess_cmd(command):
   process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
   proc_stdout = process.communicate()[0].strip()
   return proc_stdout

if __name__ == '__main__':

   COMMANDS          = []
   ENV_NAME          = 'meleeai'

   TARGET_PLATFORM   = platform.system().lower()
   TARGET_PYTHON     = sys.version_info
   PYTHON_BIT        = (struct.calcsize("P") * 8)

   if PYTHON_BIT not in [32, 64]:
      print('Invalid bit version passed, exiting.')
      exit(1)

   if (3, 5) <= TARGET_PYTHON >= (3, 8):
      print('Invalid Python Version Used: {}, build is terminating.'.format(sys.version))
   else:
      # Setup the virtualenv
      PYTHON_EXECUTABLE    = '"' + sys.executable.replace('\\', '/') + '"'                            # `repr` was returning [0], [-1] ticks
      COMMANDS.append('%s -m pip install virtualenv==16.06 --user' % PYTHON_EXECUTABLE)
      COMMANDS.append('%s -m virtualenv %s' % (PYTHON_EXECUTABLE, ENV_NAME))
      ENV_NAME             = '%s/%s' % (os.getcwd().replace('\\', '/'), ENV_NAME)
      if TARGET_PLATFORM == 'windows':
         PYTHON_EXECUTABLE = '%s\\Scripts\\python.exe' % ENV_NAME
         COMMANDS.append('%s -m pip install -e .' % PYTHON_EXECUTABLE)
         COMMANDS.append('%s/Scripts/sphinx-apidoc.exe -o docs/source/ src/' % ENV_NAME)
         sys.path.insert(0, 'meleeai/Scripts/')
      elif TARGET_PLATFORM == 'linux':
         PYTHON_EXECUTABLE = '%s/bin/python' % ENV_NAME
         COMMANDS.append('%s -m pip install -e .' % PYTHON_EXECUTABLE)
         COMMANDS.append('%s/bin/sphinx-apidoc -o docs/source/ src/' % ENV_NAME)
         sys.path.insert(0, 'meleeai/Scripts/')
      else:
         print('Unsupported Platform: {}, build is terminating.'.format(TARGET_PLATFORM))

   COMMANDS.append(('%s/Scripts/activate.bat; cd docs/; make.bat html; cd ..' % ENV_NAME))

   for command in COMMANDS:
      if isinstance(command, str):
         print('>> %s' % command)
         if subprocess.run(command).returncode != 0:
            print('Command:\t%s failed!' % command)
            exit(1)
      else:
         subprocess_cmd(command)

   # TODO: Set an environmental variable pointing to meleeai/Scripts or meleeai/bin for Sphinx
   print('Build complete!\nTo generate the documentation, enter docs/ and run `make html`.')