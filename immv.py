#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os.path
import shutil

class FileNotFoundException(Exception):
  def __init__(self, filename):
    self.filename= filename
  def __str__(self):
    return repr(self.filename)



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


def check_files_exist(filenames):
  for f in filenames:
    if not os.path.lexists(f):
      raise FileNotFoundException(f)


def callEditorForEditing(fn_string):
  return []


def get_files_to_rename(old_files, new_files):
  if len(old_files) != len(new_files):
    raise Exception("Error: Number of filenames changed. Cannot proceed.")

  files_to_rename= []
  for i in range(0, len(old_files)):
    if old_files[i] != new_files[i]:
      files_to_rename.append((old_files[i], new_files[i]))
  
  return files_to_rename


if __name__ == "__main__":
  #parse Kommandozeile
  (options, args)= parseCommandline()
  #prüfe, ob auch wirklich alles Dateinamen sind
  try:
    #Erstelle String aus Dateinamen
    fn_string= filenames_to_string(args)
    #zeige Editor mit fn_strings
    changedFileNames= callEditorForEditing(fn_string)
    rename_list= get_files_to_rename(args, changedFileNames)

    for t in rename_list:
    #TODO: prüfe, ob destfile schon existiert + Exception
      shutil.move(t[0], t[1])
      
  except FileNotFoundException, e:
    print "file not found: "+e.filename
    exit(1)
  except Exception, e:
    print e

#  file_list= get_file_list(args)
#  print file_list
  #Zeige String in $EDITOR
  #prüfe Anzahl Zeilen in origString + newString
  #mache Änderungen
