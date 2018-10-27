#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import string

# Use word_tokenize to split raw text into words
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize



scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)



class LimerickDetector:

    def __init__(self):
        """
        Initializes the object to have a pronunciation dictionary available
        """
        self._pronunciations = nltk.corpus.cmudict.dict()
        """
        API Documentation for CMU dictionary corpus
        http://www.nltk.org/api/nltk.corpus.reader.html#module-nltk.corpus.reader.cmudict
        """

    def num_syllables(self, word):
        """
        Returns the number of syllables in a word.  If there's more than one
        pronunciation, take the shorter one.  If there is no entry in the
        dictionary, return 1.
        """
        """
        using the logic of vowel counting, count all vowels in the pronunciations
        """
        dictionary = self._pronunciations;
        # check if word is present in the CMU dictionary
        if word in dictionary :
          word_pronunciations = dictionary[word.lower()]
        else :
          return 1
        
        vowels = ['A', 'E', 'I', 'O', 'U']
        
        ## find the shorter pronunciation for word
        shorter_arr = [];
        for pronunciation in word_pronunciations :
           if len(pronunciation) > len(shorter_arr) : shorter_arr = pronunciation
        
        num_length = 0
        
        for phoneme in shorter_arr :
          if phoneme[:1] in vowels : num_length += 1
        
        return num_length
           

    def rhymes(self, a, b):
        """
        Returns True if two words (represented as lower-case strings) rhyme,
        False otherwise.
        """
        # match everything after the first 1 for all combinations
        # check if a is present in the CMU dictionary
        if a in self._pronunciations :
          a_pronunciations = self._pronunciations[a.lower()]
        else :
          return False
        
         # check if b is present in the CMU dictionary
        if b in self._pronunciations :
          b_pronunciations = self._pronunciations[b.lower()]
        else :
          return False
       
        
        ret_val = False
        a_string = "" 
        b_string = ""
        for a_pronunciation in a_pronunciations:
          a_string = ""  
          for phoneme in a_pronunciation : 
            a_string += phoneme
          for b_pronunciation in b_pronunciations: 
            b_string = ""  
            for phoneme in b_pronunciation : 
              b_string += phoneme
            
            if "1" in a_string :
              a_string = a_string[a_string.index("1"):]
            if "1" in b_string :
              b_string = b_string[b_string.index("1"):]

            if a_string == b_string : 
              ret_val = True
            
        return ret_val
            
        
    def is_limerick(self, text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          * No two A lines should differ in their number of syllables by more than two.
          * The B lines should differ in their number of syllables by no more than two.
          * Each of the B lines should have fewer syllables than each of the A lines.
          * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)


        """
        
        sentences = text.splitlines()
        
        #remove blank setences
        sentences = [sentence for sentence in sentences if sentence.strip()] 
        
        if len(sentences) != 5 :  return False 
        #remove punctuations for all sentences
        words_sentence1 = word_tokenize(sentences[0].translate(None, string.punctuation).lower())
        words_sentence2 = word_tokenize(sentences[1].translate(None, string.punctuation).lower())
        words_sentence3 = word_tokenize(sentences[2].translate(None, string.punctuation).lower())
        words_sentence4 = word_tokenize(sentences[3].translate(None, string.punctuation).lower())
        words_sentence5 = word_tokenize(sentences[4].translate(None, string.punctuation).lower())
        
        #check rhymes for AAA BB and not rhymes for AB
        ret_flag = (self.rhymes(words_sentence1[len(words_sentence1) - 1],
           words_sentence2[len(words_sentence2) - 1]) and
           self.rhymes(words_sentence3[len(words_sentence3) - 1 ],
           words_sentence4[len(words_sentence4) - 1 ]) and
           self.rhymes(words_sentence2[len(words_sentence2) - 1 ],
           words_sentence5[len(words_sentence5) - 1 ]) and
           self.rhymes(words_sentence1[len(words_sentence1) - 1 ],
           words_sentence5[len(words_sentence5) - 1 ]) and 
           (not self.rhymes(words_sentence1[len(words_sentence1) - 1],
           words_sentence3[len(words_sentence3) - 1])) and 
           (not self.rhymes(words_sentence1[len(words_sentence1) - 1],
           words_sentence4[len(words_sentence4) - 1])) and 
           (not self.rhymes(words_sentence2[len(words_sentence2) - 1],
           words_sentence3[len(words_sentence3) - 1])) and 
           (not self.rhymes(words_sentence2[len(words_sentence2) - 1],
           words_sentence4[len(words_sentence4) - 1])) and 
           (not self.rhymes(words_sentence5[len(words_sentence5) - 1],
           words_sentence3[len(words_sentence3) - 1])) and 
           (not self.rhymes(words_sentence5[len(words_sentence5) - 1],
           words_sentence4[len(words_sentence4) - 1])))
          
        if ret_flag == False: return False
        
        
        # Check additional constraints
        
        sum_of_syl1 = 0
        for word in words_sentence1 : sum_of_syl1 += self.num_syllables(word)
       
        if sum_of_syl1 < 4 : return False
        sum_of_syl2 = 0
        for word in words_sentence2 : sum_of_syl2 += self.num_syllables(word)
        
        if sum_of_syl2 < 4 : return False
          
        
        sum_of_syl_A_diff = 0
        if sum_of_syl1 > sum_of_syl2 : sum_of_syl_A_diff = sum_of_syl1 - sum_of_syl2
        else : sum_of_syl_A_diff = sum_of_syl2 - sum_of_syl1
       
        if sum_of_syl_A_diff > 2 : return False 
        
        sum_of_syl3 = 0
        for word in words_sentence3 : sum_of_syl3 += self.num_syllables(word)
       
        if sum_of_syl3 < 4 : return False
        sum_of_syl4 = 0
        for word in words_sentence4 : sum_of_syl4 += self.num_syllables(word)
       
        if sum_of_syl4 < 4 : return False
          
        
        sum_of_syl_B_diff = 0
        if sum_of_syl3 > sum_of_syl4 : sum_of_syl_B_diff = sum_of_syl3 - sum_of_syl4
        else : sum_of_syl_B_diff = sum_of_syl4 - sum_of_syl3
        
        if sum_of_syl_B_diff > 2 : return False 
            
        if (sum_of_syl3 > sum_of_syl1 and sum_of_syl3 > sum_of_syl2 
           and sum_of_syl4 > sum_of_syl1 and sum_of_syl4 > sum_of_syl2) :  return False
                    
                    
        sum_of_syl5 = 0
        for word in words_sentence5 : sum_of_syl5 += self.num_syllables(word) 
       
        if sum_of_syl5 < 4 : return False
        
        sum_of_syl_A_diff = 0
        if sum_of_syl1 > sum_of_syl5 : sum_of_syl_A_diff = sum_of_syl1 - sum_of_syl5
        else : sum_of_syl_A_diff = sum_of_syl5 - sum_of_syl1
        
        if sum_of_syl_A_diff > 2 : return False 
        
        sum_of_syl_A_diff = 0
        if sum_of_syl2 > sum_of_syl5 : sum_of_syl_A_diff = sum_of_syl2 - sum_of_syl5
        else : sum_of_syl_A_diff = sum_of_syl5 - sum_of_syl2
        
        
        if sum_of_syl_A_diff > 2 : return False 
        
        if (sum_of_syl3 > sum_of_syl5 and sum_of_syl4 > sum_of_syl5) :  return False
       
      
        return ret_flag
              
            

    # TODO: if implementing guess_syllables add that function here by uncommenting the stub code and
    # completing the function. If you want guess_syllables to be used by num_syllables, feel free to integrate it appropriately.
    #
    # def guess_syllables(self, word):
    #   """
    #   Guesses the number of syllables in a word. Extra credit function.
    #   """
    #   # TODO: provide an implementation!
    #   pass

    # TODO: if composing your own limerick, put it here and uncomment this function. is_limerick(my_limerick()) should be True
    #
    #
    # def my_limerick(self):
    #   """
    #   A limerick I wrote about computational linguistics
    #   """
    #   limerick="""
    #     Replace these words
    #     with your limerick
    #     and then test it out
    #   """
    #   return limerick


# The code below should not need to be modified
def main():
  parser = argparse.ArgumentParser(description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")




  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  ld = LimerickDetector()
  lines = ''.join(infile.readlines())
  outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))

if __name__ == '__main__':
  main()