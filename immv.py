#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import os.path
import subprocess
import shutil
import tempfile

class FileNotFoundException(Exception):
  def __init__(self, filename):
    self.filename= filename
  def __str__(self):
    return repr(self.filename)

class FileCountChangedException(Exception):
  def __init__(self, orig_count, new_count):
    self.orig_count= orig_count
    self.new_count= new_count
  def __str__(self):
    return "original count="+str(self.orig_count)+", new count="+str(self.new_count)


def parseCommandline():
  usage= "usage: %prog [options] FILES"
  parser= OptionParser(usage=usage)
  parser.add_option("-a", "--ask", dest="needs_confirmation", default=False,
                    action="store_true",
                    help="ask for confirmation before doing anything")
  parser.add_option("-q", "--quiet", dest="verbose", default=True,
                    action="store_false",
                    help="don't output anything, except error messages")

  (options, args)= parser.parse_args()
  return (options, args)


def get_file_list(filenames):
  file_list= []
  for f in filenames:
    file_list.append(open(f))
  return file_list


def filenames_to_string(filenames):
  fn_string= ""
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)
    fn_string+= os.path.basename(f)+"\n"
  return fn_string

def get_base_file_names(filenames):
  base_file_names= []
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)
    base_file_names.append(os.path.basename(f))
  return base_file_names


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


def callEditorForEditing(temp_file):
  env_editor= os.getenv("EDITOR")
  if env_editor is None:
    #FIXME: is this too debian specific
    env_editor='sensible-editor'
  retcode= subprocess.call([env_editor, temp_file.name])


def get_files_to_rename(old_files, new_files):
  if len(old_files) != len(new_files):
    raise FileCountChangedException(len(old_files), len(new_files))

  files_to_rename= []
  for i in range(0, len(old_files)):
    if old_files[i] != new_files[i]:
      files_to_rename.append((old_files[i], new_files[i]))
  
  return files_to_rename

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


if __name__ == "__main__":
  #parse Kommandozeile
  (options, args)= parseCommandline()
  #prüfe, ob auch wirklich alles Dateinamen sind
  try:
#    #Erstelle String aus Dateinamen
#    fn_string= filenames_to_string(args)
#    base_file_names= get_base_file_names(args)
#    paths_of_file_names= get_paths_of_file_names(args)
    paths, base_file_names= split_path_and_filenames(args)

    #erzeuge temp_file
    temp_file= get_temp_file()
    fill_temp_file(base_file_names, temp_file)

    #zeige Editor mit temp_file
    callEditorForEditing(temp_file)

    #lies geändertes temp_file
    temp_file.seek(0)
    lines= temp_file.readlines()
    temp_file.close()
    new_file_names= strip_eol(lines)

    for path, orig_filename, new_filename in \
        zip(paths, base_file_names, new_file_names):
      print "P: %s, OFN: %s, NFN: %s" % (path, orig_filename, new_filename)
      if not orig_filename == new_filename:
        #TODO: prüfe, ob destfile schon existiert + Exception
        shutil.move(os.path.join(path, orig_filename),\
                    os.path.join(path, new_filename))
      
  except FileNotFoundException, e:
    print "Error! File not found: "+e.filename
    exit(1)
  except FileCountChangedException, e:
    print "ERROR! Number of files changed: ",e
    exit(2)

#  file_list= get_file_list(args)
#  print file_list
  #Zeige String in $EDITOR
  #prüfe Anzahl Zeilen in origString + newString
  #mache Änderungen
