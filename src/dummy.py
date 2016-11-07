from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True


def dnaSequence(sequence):
  n = int(len(sequence)/4)
  substrings = 0
  for k in xrange(1, n+1):
    s = score(sequence[:4*k])
    if check_score(s):
      substrings += 1
    for i in xrange(1,len(sequence)-4*k+1):
      s[sequence[i-1]] -= 1
      s[sequence[i+4*k-1]] += 1
      # print(sequence[i:i+4*k],s)
      if check_score(s):
        substrings += 1
  # print(substrings)
  return substrings

seenMap = {}
def is_valid_wrapper(sequence):
  validity = seenMap.get(sequence, None)
  if validity is None:
    validity = isValid(sequence)
    seenMap[sequence] = validity
  return validity

def score(sequence):
  s = {
    'A':0,'C':0,'G':0,'T':0
  }
  for char in sequence:
    s[char] += 1
  return s

def check_score(s):
  return s['A'] == s['C'] == s['G'] == s['T']

def isValid(sequence):
  a,c,g,t = 0,0,0,0
  for char in sequence:
    if char == 'A': a+=1
    elif char == 'C': c+=1
    elif char == 'G': g += 1
    elif char == 'T': t += 1
  return a==c==g==t

dnaSequence("ACGTACGT")
