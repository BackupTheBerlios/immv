#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Interactictive Multi MoVe

   Rename multiple files at once by editing their names in
   a text editor.
"""

__author__ = "Marco Herrn <marco@mherrn.de>"
__version__= "0.1"
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

################################################################
##
## Exceptions
##

class FileNotFoundException(Exception):
  def __init__(self, filename):
    Exception.__init__(self)
    self.filename= filename
  def __str__(self):
    return repr(self.filename)

class FileCountChangedException(Exception):
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

  (options, args)= parser.parse_args()

  #FIXME: Shouldn't this be moved to check_args()?
  #       But then the parser needs to be global
  if len(args) == 0:
    parser.print_help()
    exit(_EXIT_STATUS_ABORT)

  return (options, args)


def _split_path_and_filenames(filenames):
  paths= []
  base_file_names= []
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)
    path, basename= os.path.split(f)
    paths.append(path)
    base_file_names.append(basename)
  return paths, base_file_names
    

def _check_files_exist(filenames):
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)


def _call_editor(temp_file):
  env_editor= os.getenv("EDITOR")
  if env_editor is None:
    #FIXME: is this too debian specific?
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
  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    orig_path= os.path.join(path, orig_filename)
    new_path= os.path.join(path, new_filename)
    if not orig_filename == new_filename:
      _info(orig_path + ": -> " + new_path, options)
    else:
      _info(orig_path + ": no change", options)


def _do_rename(paths, base_file_names, new_file_names, options):
  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    orig_path= os.path.join(path, orig_filename)
    new_path= os.path.join(path, new_filename)
    if orig_filename == new_filename:
      _info("No change to file "+orig_path, options)
    else:
      skip_file= False
      if os.path.lexists(new_path):
        if options.interactive:
          confirmed= _ask_for_overwrite(orig_path, new_path)
          if not confirmed:
            _info("Skipped file "+orig_path, options)
            skip_file= True
        elif not options.overwrite_files:
          _info("Skipped file "+orig_path+" (target name exists)", options)
          skip_file= True

      #again test if the orig file still exists
      if not os.path.lexists(orig_path):
        _error("Error! File "+orig_path+" doesn't exist anymore?")
        skip_file= True

      if not skip_file:
        _info("Rename file "+orig_path+" -> "+new_path, options)
        try:
          shutil.move(orig_path, new_path)
        except Exception, e:
          _error("+Unexpected Error! "+repr(e)+"\n+Please file a bug report.")


def _ask_for_overwrite(old_file, new_file):
  answer= raw_input(old_file+" -> "+new_file+"\n"+ \
                      new_file+" exists. Overwrite? (y/N):")
  if answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
    return True
  else:
    return False


def _info(string, options):
  """Prints an informational message, unless --quiet was set"""
  if options.verbose:
    print string

def _error(string):
  """Prints an error message to stderr. 
     The --quiet option doesn't avoid this."""
  sys.stderr.write(string+"\n")


################################################################
##
## main
##

if __name__ == "__main__":
  #parse Kommandozeile
  (options, args)= _parse_commandline()
  try:
    _check_files_exist(args)
  except FileNotFoundException, e:
    _error("Error! File not found: "+e.filename)
    exit(_EXIT_STATUS_ABORT)

  try:
    #Trenne Pfade von Dateinamen
    paths, base_file_names= _split_path_and_filenames(args)

    #Erzeuge temp_file
    temp_file= _get_temp_file()
    _fill_temp_file(base_file_names, temp_file)

    #Zeige Editor mit temp_file
    _call_editor(temp_file)

    #Lies geändertes temp_file
    temp_file.seek(0)
    lines= temp_file.readlines()
    temp_file.close()
    new_file_names= _strip_eol(lines)


    #Führe das Umbenennen durch
    if options.needs_confirmation:
      _simulate_rename(paths, base_file_names, new_file_names, options)
      answer= raw_input("Continue with rename? (y/N): ")
      if not answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
        exit(_EXIT_STATUS_ABORT)
    _do_rename(paths, base_file_names, new_file_names, options)
      
  except FileNotFoundException, e:
    _error("Error! File not found: "+e.filename)
    exit(_EXIT_STATUS_ERROR)
  except FileCountChangedException, e:
    _error("Error! Number of files changed: ",e)
    exit(_EXIT_STATUS_ABORT)

