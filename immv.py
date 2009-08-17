#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import os.path
import subprocess
import shutil
import tempfile
import readline


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

def parse_commandline():
  usage= "usage: %prog [options] FILES"
  parser= OptionParser(usage=usage)
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
  return (options, args)


def split_path_and_filenames(filenames):
  paths= []
  base_file_names= []
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)
    path, basename= os.path.split(f)
    paths.append(path)
    base_file_names.append(basename)
  return paths, base_file_names
    

def check_files_exist(filenames):
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)


def call_editor(temp_file):
  env_editor= os.getenv("EDITOR")
  if env_editor is None:
    #FIXME: is this too debian specific
    env_editor='sensible-editor'
  retcode= subprocess.call([env_editor, temp_file.name])


def get_temp_file():
  return tempfile.NamedTemporaryFile(mode='w+')


def fill_temp_file(old_files, temp_file):
  print 1
  for f in old_files:
    print 2
    temp_file.write(f+"\n")
  print 3
  temp_file.flush()


def strip_eol(list_of_strings):
  stripped= []
  for item in list_of_strings:
    stripped.append(item.strip())
  return stripped


def do_rename(paths, base_file_names, new_file_names, options):
  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    if orig_filename == new_filename:
      info("No change to file "+os.path.join(path, old_filename))
    else:
      skip_file= False
      if os.path.lexists(os.path.join(path, new_filename)):
        if 'interactive' in options:
          confirmed= ask_for_overwrite(os.path.join(path, orig_filename),\ 
                                       os.path.join(path, new_filename))
          if not confirmed:
            info("Skipped file "+os.path.join(path, orig_filename))
            skip_file= True
        elif not 'overwrite' in options:
          info("Skipped file "+os.path.join(path, orig_filename))
          skip_file= True
      
      if not skip_file:
        shutil.move(os.path.join(path, orig_filename),\
                      os.path.join(path, new_filename))


def ask_for_overwrite(old_file, new_file):
  answer= raw_input(old_file+" -> "+new_file+"\n"+ \
                      new_file+" exists. Overwrite? (y/N):")
  if answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
    return True
  else:
    return False


def info(string, options):
  """Prints an informational message, unless --quiet was set"""
  if "verbose" in options:
    print string


def simulate_rename(paths, base_file_names, new_file_names):
  for path, orig_filename, new_filename in \
      zip(paths, base_file_names, new_file_names):
    if not orig_filename == new_filename:
      print os.path.join(path, orig_filename)+": -> "+ \
            os.path.join(path, new_filename)
    else:
      print os.path.join(path, orig_filename)+": no change"



################################################################
##
## main
##

if __name__ == "__main__":
  #parse Kommandozeile
  (options, args)= parse_commandline()
  #prüfe, ob auch wirklich alles Dateinamen sind
  try:
    #Trenne Pfade von Dateinamen
    paths, base_file_names= split_path_and_filenames(args)

    #Erzeuge temp_file
    temp_file= get_temp_file()
    fill_temp_file(base_file_names, temp_file)

    #Zeige Editor mit temp_file
    call_editor(temp_file)

    #Lies geändertes temp_file
    temp_file.seek(0)
    lines= temp_file.readlines()
    temp_file.close()
    new_file_names= strip_eol(lines)


    #Führe das Umbenennen durch
    if 'needs_confirmation' in options:
      simulate_rename(paths, base_file_names, new_file_names)
      answer= raw_input("Continue with rename? (y/N): ")
      if not answer in ('y', 'Y', 'yes', 'Yes', 'YES'):
        exit(9)
    do_rename(paths, base_file_names, new_file_names)
      
  except FileNotFoundException, e:
    print "Error! File not found: "+e.filename
    exit(2)
  except FileCountChangedException, e:
    print "ERROR! Number of files changed: ",e
    exit(3)

