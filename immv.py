#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Interactictive Multi MoVe

   Rename multiple files at once by editing their names in
   a text editor.

"""

__author__ = "Marco Herrn <marco@mherrn.de>"
__version__= "0.3"
__license__= "GPL"

from optparse import OptionParser
import sys
import os
import os.path
import subprocess
import shutil
import tempfile
import readline

_EXIT_STATUS_OK= 0
_EXIT_STATUS_ABORT= 1
_EXIT_STATUS_ERROR= 2

_MARK_ERROR=  "!"
_MARK_CHANGE= "+"
_MARK_SKIP=   " "

################################################################
##
## Exceptions
##

class FileNotFoundException(Exception):
  """Thrown when trying to rename a file that doesn't exist.

  """
  def __init__(self, filename):
    Exception.__init__(self)
    self.filename= filename
  def __str__(self):
    return repr(self.filename)


class FileCountChangedException(Exception):
  """Thrown when the number of files after editing has
  changed. 
  This is usually an accident.

  """
  def __init__(self, orig_count, new_count):
    Exception.__init__(self)
    self.orig_count= orig_count
    self.new_count= new_count
  def __str__(self):
    return "original count="+str(self.orig_count)+\
           ", new count="+str(self.new_count)

################################################################
##
## Functions
##

def _parse_commandline():
  usage= "usage: %prog [options] FILES"
  version= "%prog -Interactive Multi MoVe- "+__version__
  parser= OptionParser(usage=usage, version=version)
  parser.add_option("-a", "--ask", dest="needs_confirmation", default=False,
                    action="store_true",
                    help="ask for confirmation before doing anything")
  parser.add_option("-q", "--quiet", dest="verbose", default=True,
                    action="store_false",
                    help="don't output anything, except error messages")
  parser.add_option("-o", "--overwrite", dest="overwrite_files", default=False,
                    action="store_true",
                    help="overwrite existing files")
  parser.add_option("-i", "--interactive", dest="interactive", default=False,
                    action="store_true",
                    help="ask for confirmation before overwriting existing files")
  parser.add_option("-e", "--editor", dest="editor",
                    help="editor to use for editing the filenames")

  (options, args)= parser.parse_args()

  #FIXME: Shouldn't this be moved to check_args()?
  #       But then the parser needs to be global
  if len(args) == 0:
    parser.print_help()
    exit(_EXIT_STATUS_ABORT)

  return (options, args)


def _split_path_and_filenames(filenames):
  """Split a list full pathnames into their paths and base filenames.

  filenames -- a list of filenames with or without paths
  
  Returns a tuple with a list of all the paths and a list of all the
  base filenames. These two lists are both exactly as long as the
  parameter 'filenames'.

  This function also checks if the given files actually exist. If a file 
  (or more than one) is not found in the system a FileNotFoundException
  is raised for the first missing file.

  """

  paths= []
  base_file_names= []
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)
    if os.path.isdir(f):
      f= _strip_trailing_slash(f)
    path, basename= os.path.split(f)
    if os.path.isdir(f):
      basename=basename+'/'
    paths.append(path)
    base_file_names.append(basename)
  return paths, base_file_names


def _strip_trailing_slash(dirname):
  """Strip the trailing slash from a directory path

  If the given directory name ends with a slash, it is removed. Otherwise
  nothing is done.
  There is no check whether this is a real directory or a valid dir name.

  Returns the dirname without a trailing slash.

  """
  if dirname.endswith('/'):
    return dirname[:-1]
  else:
    return dirname


def _check_files_exist(filenames):
  """Check if all files in a given list actually exist.

  filenames -- a list of filenames with or without path to check

  If at least one file is not found, a FileNotFoundException is
  raised for the first missing file.

  This function doesn't return any value.

  """

  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)


def _call_editor(temp_file):
  env_editor= None
  if options.editor:
    env_editor= options.editor
  if env_editor is None:
    env_editor= os.getenv("EDITOR")
  if env_editor is None:
    env_editor='sensible-editor'
  retcode= subprocess.call([env_editor, temp_file.name])


def _get_temp_file():
  return tempfile.NamedTemporaryFile(mode='w+')


def _fill_temp_file(old_files, temp_file):
  for f in old_files:
    temp_file.write(f+"\n")
  temp_file.flush()


def _strip_eol(list_of_strings):
  stripped= []
  for item in list_of_strings:
    stripped.append(item.strip())
  return stripped


def _simulate_rename(paths, base_file_names, new_file_names):
  """Simulate the renaming that would actually be done.

  This method prints out the original filenames with their path
  and what would be done to them. Either no change or the name
  of the resulting file with its path.

  paths -- the pathnames of the files given
  base_file_names -- the base file names without path of the
                     original files
  new_file_names -- the base file names of the resulting files

  """

  if len(base_file_names) != len(new_file_names):
    raise FileCountChangedException(len(base_file_names), len(new_file_names))

  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    orig_path= os.path.join(path, orig_filename)
    new_path= os.path.join(path, new_filename)
    if not orig_filename == new_filename:
      _print_action(_MARK_CHANGE, options.padding, orig_path, new_path)
    else:
      _print_action(_MARK_SKIP, options.padding, orig_path, new_path)


def _do_rename(paths, base_file_names, new_file_names):
  if len(base_file_names) != len(new_file_names):
    raise FileCountChangedException(len(base_file_names), len(new_file_names))

  error_in_processing= False

  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    orig_path= os.path.join(path, orig_filename)
    new_path= os.path.join(path, new_filename)
    if orig_filename == new_filename:
      _print_action(_MARK_SKIP, options.padding, orig_path, new_path)
    else:
      skip_file= False
      if os.path.lexists(new_path):
        if options.interactive:
          confirmed= _ask_for_overwrite(orig_path, new_path)
          if not confirmed:
            _print_action(_MARK_SKIP, options.padding, orig_path, new_path)
            skip_file= True
        elif not options.overwrite_files:
          _print_action(_MARK_SKIP, options.padding, orig_path, new_path, "Target name exists")
          skip_file= True

      #again test if the orig file still exists
      if not skip_file and not os.path.lexists(orig_path):
        _print_action(_MARK_ERROR, options.padding, orig_path, new_path, "File doesn't exist anymore?")
        skip_file= True
        error_in_processing= True

      if not skip_file:
        try:
          shutil.move(orig_path, new_path)
          _print_action(_MARK_CHANGE, options.padding, orig_path, new_path)
        except IOError, e:
          _print_action(_MARK_ERROR, options.padding, orig_path, new_path, os.strerror(e.errno))
          error_in_processing= True
        except Exception, e:
          _print_action(_MARK_ERROR, options.padding, orig_path, new_path, os.strerror(e.errno))
          _error("+Unexpected Error! "+repr(e)+"\n+Please file a bug report.")
          error_in_processing= True

  if error_in_processing:
    return _EXIT_STATUS_ERROR
  else:
    return _EXIT_STATUS_OK


def _ask_for_overwrite(old_file, new_file):
  answer= raw_input(old_file+" -> "+new_file+"\n"+ \
                      new_file+" exists. Overwrite? (y/N):")
  if answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
    return True
  else:
    return False


def _info(string):
  """Prints an informational message, unless --quiet was set"""
  if options.verbose:
    print string
  

def _error(string):
  """Prints an error message to stderr. 
     The --quiet option doesn't avoid this."""
  sys.stderr.write(string+"\n")
    
    
def _print_action(type, padding, orig_filename, new_filename, comment=None):
  if options.verbose:
    if type == _MARK_SKIP:
      template= "%c %-"+str(padding)+"s"
      print template % (type, orig_filename),
    else:
      template = "%c %-"+str(padding)+"s  -->  %s"
      print template % (type, orig_filename, new_filename),
    if comment:
      print "- "+str(comment),
    print ""


def _get_max_len(list_of_strings):
  max_len= 0;
  for string in list_of_strings:
    max_len= max(max_len, len(string))
  return max_len


################################################################
##
## main
##

if __name__ == "__main__":
  global options
  (options, args)= _parse_commandline()
  paths, base_file_names= None, None
  try:
    _check_files_exist(args)
    paths, base_file_names= _split_path_and_filenames(args)
  except FileNotFoundException, e:
    _error("Error! File not found: "+e.filename)
    exit(_EXIT_STATUS_ABORT)

  #create the temporary file to work on
  temp_file= _get_temp_file()
  _fill_temp_file(base_file_names, temp_file)

  mtime_before= os.path.getmtime(temp_file.name)

  try:
    _call_editor(temp_file)
  except OSError, e:
    _error("Error calling editor: "+e.strerror)
    exit(_EXIT_STATUS_ABORT)

  if os.path.getmtime(temp_file.name) == mtime_before:
    # _debug("Nothing changed.")
    exit(_EXIT_STATUS_ABORT)

  #Read the edited temp_file
  temp_file.seek(0)
  lines= temp_file.readlines()
  temp_file.close()
  new_file_names= _strip_eol(lines)


  #count length of orig_filenames
  options.padding= str(_get_max_len(args))

  #Now do the rename
  try:
    if options.needs_confirmation:
      _simulate_rename(paths, base_file_names, new_file_names)
      answer= raw_input("Continue with rename? (y/N): ")
      if not answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
        exit(_EXIT_STATUS_ABORT)
    exit_code= _do_rename(paths, base_file_names, new_file_names)
    exit(exit_code)
  except FileCountChangedException, e:
    _error("Error! Number of files changed")
#    _debug("Original filecount: "+str(e.orig_count)+ \
#           "new filecount: "+str(e.new_count))
    exit(_EXIT_STATUS_ABORT)
