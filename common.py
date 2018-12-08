#!/usr/bin/python
#Utility fuctions used by other scripts

# Installation of model:
  # pip install --user https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz

import csv, re, argparse, string, hashlib, json, gzip, copy, itertools, os, math, sys, random, socket, struct, pprint
from timeit import default_timer as timer
from itertools import chain, combinations
from functools import reduce
from collections import defaultdict
# import blist
import pickle
import zlib

import spacy
from nltk.util import ngrams
from sortedcontainers import SortedList, SortedDict
from jsonstreamer import JSONStreamer

SOCK_IP   = "127.0.0.1"
SOCK_PORT = 50507

STOPWORDS = {
  'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during',
  'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours',
  'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as',
  'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your',
  'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should',
  'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when',
  'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does',
  'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now',
  'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those',
  'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing',
  'it', 'how', 'further', 'was', 'here', 'than'
  }

ALPHA        = 'abcdefghijklmnopqrstuvwxyz'
RE_WORD      = re.compile(r"""[\-\'a-zA-Z]{2,}""")
DEFAULTTUPLE = [0,9999,9999]

_debug          = True

#Colors
class col:
  BLN = '\033[0m'    # Blank
  UND = '\033[1;4m'  # Underlined
  INV = '\033[1;7m'  # Inverted
  CRT = '\033[1;41m' # Critical
  BLK = '\033[1;30m' # Black
  RED = '\033[1;31m' # Red
  GRN = '\033[1;32m' # Green
  YLW = '\033[1;33m' # Yellow
  BLU = '\033[1;34m' # Blue
  MGN = '\033[1;35m' # Magenta
  CYN = '\033[1;36m' # Cyan
  WHT = '\033[1;37m' # White

# Useful printing codes (long)
def inptp(s):
  return input(col.WHT+"["+col.BLU+"input"+col.WHT+"] "+str(s)+col.BLN)
def infop(s):
    print(col.WHT+"["+col.GRN+" info"+col.WHT+"] "+col.BLN+str(s))
def logfp(s,logf=None):
    print(col.WHT+"["+col.MGN+"  log"+col.WHT+"] "+col.BLN+str(s))
    if logf is not None: logf.write(str(s)+"\n")
def dbugp(s):
  if _debug:
    print(col.WHT+"["+col.BLK+"debug"+col.WHT+"] "+col.BLN+str(s))
def simup(s):
  if _simulate:
    print(col.WHT+"["+col.CYN+"simul"+col.WHT+"] "+col.BLN+str(s))
def warnp(s):
    print(col.WHT+"["+col.YLW+" warn"+col.WHT+"] "+col.BLN+str(s))
def erorp(s):
    sys.stderr.write(col.WHT+"["+col.RED+"error"+col.WHT+"] "+col.BLN+str(s)+"\n")
def sendp(s):
    print(col.WHT+"["+col.CYN+" send"+col.WHT+"] "+s+col.BLN)
def recvp(s):
    print(col.WHT+"["+col.CYN+" recv"+col.WHT+"] "+s+col.BLN)
def passp(s):
  return getpass(col.WHT+"["+col.BLU+"paswd"+col.WHT+"] "+str(s)+col.BLN)

#Timer decorator for method execution time
def timeit(method):
  def timed(*args, **kw):
    start = timer()
    result = method(*args, **kw)
    end = timer()
    dbugp("  Took {} seconds".format(end-start))
    return result
  return timed

#Write a list of dictionaries to a CSV
def writeDictToCsv(file,headerfields,datadict):
  with open(file,'w') as fout:
    writer = csv.writer(fout,delimiter='\t')
    writer.writerow(headerfields)
    for entry in datadict:
      writer.writerow([entry[f] if f in entry else "" for f in headerfields])

#Load a CSV into a list of dictionaries or dictionary of dictionaries
def loadCsvAsDict(file,ikey=None):
  with open(file,"r") as csvfile:
    reader = csv.reader((x.replace('\0', ' ') for x in csvfile),delimiter='\t',quoting=csv.QUOTE_NONE)
    fields = next(reader)
    ikey = None if not ikey in fields else fields.index(ikey)
    if ikey is None:
      return [ { f : row[i] for i,f in enumerate(fields) } for row in reader ]
    return { row[ikey] : { f : row[i] for i,f in enumerate(fields) } for row in reader}

#Create a directory and all children necessary
def makedir(directory):
  os.makedirs(directory,exist_ok=True)

#Write a JSON to a file
def jsonWrite(data,filename,indent=2):
  with open(filename, 'w') as fout:
    fout.write(json.dumps(data,indent=indent))
    # pprint.PrettyPrinter(width=118,indent=indent,stream=fout).pprint(data)

def compressedWrite(data,filename):
  with gzip.GzipFile(filename, 'w') as fout:
    fout.write(data.encode('utf-8'))

#Compress and write a JSON to a file
def compressedJsonWrite(data,filename):
  with gzip.GzipFile(filename, 'w') as fout:
    fout.write(json.dumps(data).encode('utf-8'))

#Decompress and read a JSON from a file
def compressedJsonRead(filename):
  with gzip.GzipFile(filename, 'r') as fin:
    return json.loads(fin.read().decode('utf-8'))

#Compute md5sum for string
def md5(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

# Dump an object's attributes
def dump(obj):
  for attr in dir(obj):
    try:    print("obj.%s = %r" % (attr, getattr(obj, attr)))
    except: print("obj.%s = %s" % (attr, "error"))

# Pad an ngram sequence
def pad_sequence(sequence, n, pad_left=False, pad_right=False, pad_symbol=None):
    if pad_left:
        sequence = chain((pad_symbol,) * (n-1), sequence)
    if pad_right:
        sequence = chain(sequence, (pad_symbol,) * (n-1))
    return sequence

#Generate skipgrams from a sequence
def skipgrams(sequence, n, k, **kwargs):
    """
    Returns all possible skipgrams generated from a sequence of items, as an iterator.
    Skipgrams are ngrams that allows tokens to be skipped.
    Refer to http://homepages.inf.ed.ac.uk/ballison/pdf/lrec_skipgrams.pdf

    :param sequence: the source data to be converted into trigrams
    :type sequence: sequence or iter
    :param n: the degree of the ngrams
    :type n: int
    :param k: the skip distance
    :type  k: int
    :rtype: iter(tuple)
    """

    # Pads the sequence as desired by **kwargs.
    if 'pad_left' in kwargs or 'pad_right' in kwargs:
      sequence = pad_sequence(sequence, n, **kwargs)

    # Note when iterating through the ngrams, the pad_right here is not
    # the **kwargs padding, it's for the algorithm to detect the SENTINEL
    # object on the right pad to stop inner loop.
    SENTINEL = object()
    for ngram in ngrams(sequence, n + k, pad_right=True, right_pad_symbol=SENTINEL):
      head = ngram[:1]
      tail = ngram[1:]
      for skip_tail in combinations(tail, n - 1):
          if skip_tail[-1] is SENTINEL:
              continue
          yield head + skip_tail

#Given a token, break it into idea units given as substring spans
def getRootSpan(token):
  spanmin = token.idx
  for child in token.children:
    spanmin = min(spanmin,getRootSpan(child))
  return spanmin

#Preprocess a string using our default nlp
def nlpPreprocess(nlpmodel,sentence):
  structure = {}
  structure["_tokens"] = []
  structure["_units"]  = []
  sentence             = sentence.lower()
  doc                  = nlpmodel(sentence)
  for token in doc:
    structure["_tokens"].append([ #Make sure this matches TOKEN_STRUCTURE above
        token.text,     #Plaintext of the token
        token.lemma_,   #Lemmatized word
        token.idx,      #Offset of the token into the original string
        token.dep_,     #Dependency tag for token
        token.pos_,     #Part of Speech tag for token
        token.head.idx, #Offset of parent token into the original string
      ])
    if token.dep_ == "ROOT":
      structure["_units"].append(getRootSpan(token))
  return structure

def getIdeaUnits(review):
  nunits = len(review["_units"])
  if nunits == 1:
    return [review["_tokens"]]
  units       = [ [] ]
  curunit     = 0
  nextunitpos = review["_units"][curunit+1]
  for t in review["_tokens"]:
    if t[2] >= nextunitpos: #t[2] = offset of token into string
      if (curunit < nunits-1):
        curunit += 1
        units.append([])
        nextunitpos = len(review["text"]) if (curunit == nunits-1) else review["_units"][curunit+1]
    units[-1].append(t)
  return units

def getValidTokens(tokenlist):
  validtokens = []
  for token in tokenlist:
    if not RE_WORD.search(token[0]):
      continue
    if token[1] in STOPWORDS: #Check if lemmatized version is in stopwords
      continue
    validtokens.append(token)
  return validtokens

def findNgramInSortedList(item,sortedlist):
  ipoint = sortedlist.bisect_left([item,[DEFAULTTUPLE]])
  return None if (ipoint == len(sortedlist) or (sortedlist[ipoint][0] != item)) else ipoint

def findSimilarPhrases(item,similaritydict,max_synonyms=10):
  mutations = [[] for _ in item] #Generate an empty list of mutations
  for ind,word in enumerate([w[1] for w in item]): #Use lemmatized form of each word
    if word not in similaritydict:
      continue
    for synonym in similaritydict[word][:max_synonyms]: #Get the top max_synonyms for each word and it's sim-weight
      mutations[ind].append(synonym)
  similarphrases = [[' '.join([w[1] for w in item]),1]] #Use lemmatized form of default words with weight 1.0
  for permutation in itertools.product(*mutations): #For each permutation in mutations (list of lists)
    ngram = ' '.join(p[1] for p in permutation)
    if ngram == similarphrases[0][0]:
      continue
    similarphrases.append([ #Join the ngram and multiply the weights together
        ngram,
        reduce(lambda x, y: x*y, [p[0] for p in permutation]),
      ])
  return similarphrases

#Pipeline to transform a string of text into usable NLP metadata
class NLP_Pipeline():
  def __init__(self,model=None):
    self.nlp = spacy.load('en_core_web_sm' if model is None else model)
    # self.nlp = spacy.load('en_core_web_sm')

  def processText(self,text):
    structure         = {}
    structure["text"] = text
    structure["_md5"] = md5(text)
    structure.update(nlpPreprocess(self.nlp,text))
    structure["ideaunits"] = getIdeaUnits(structure)
    structure["unigrams"]  = []
    structure["bigrams"]   = []
    structure["trigrams"]  = []
    for iu in structure["ideaunits"]: #Separate ngrams by idea unit
      iutokens = getValidTokens(iu)
      structure["unigrams"].extend(iutokens)
      structure["bigrams"].extend([g for g in skipgrams(iutokens,2,3)])
      structure["trigrams"].extend([g for g in skipgrams(iutokens,3,3)])
    return structure

#Basic socket implementation for communicating with PHP server
class MySocket:
  def __init__(self, sock=None):
    if sock is None: self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:            self.sock = sock

  def setsockopt(self,a,b,c):
    self.sock.setsockopt(a,b,c)

  def bind(self,hostport):
    self.sock.bind(hostport)

  def connect(self, host, port):
    self.sock.connect((host, port))

  def listen(self,conns):
    self.sock.listen(conns)

  def close(self):
    self.sock.close()

  def accept(self):
    return self.sock.accept()

  def sendBytes(self,message,length):
    totalsent = 0
    # print(message)
    while totalsent < length:
      sent = self.sock.send(message[totalsent:])
      if sent == 0:
        raise RuntimeError("socket connection broken")
      totalsent = totalsent + sent

  def sendInt(self,i):
    if i <= 256:
      b = struct.pack(">B",i)
      nbytes = 1
    elif i <= 65536:
      b = struct.pack(">H",i)
      nbytes = 2
    else:
      raise ValueError #TODO: can' handle
    self.sendBytes(struct.pack(">B",nbytes),1)
    self.sendBytes(b,nbytes)

  def sendFloat(self,f,length=4):
    self.sendBytes(bytearray(struct.pack("f", f)),length)

  def sendString(self, string):
    m = bytearray(string,encoding="utf-8")
    mlen = len(m)
    self.sendInt(mlen)
    self.sendBytes(m,mlen)

  def receiveBytes(self,length):
    if isinstance(length, tuple):
      length = length[0]
    chunks = []
    bytes_recd = 0
    while bytes_recd < length:
      reqn = length - bytes_recd
      if reqn < 2048:
        chunk = self.sock.recv(reqn)
      else:
        chunk = self.sock.recv(2048)
      if chunk == b'':
        raise RuntimeError("socket connection broken")
      chunks.append(chunk)
      bytes_recd = bytes_recd + len(chunk)
    bb = b''.join(chunks)
    # print(bb)
    return bb

  def receiveInt(self):
    nbytes = struct.unpack(">b",self.receiveBytes(1))[0]
    if nbytes == 1:
      return struct.unpack(">b",self.receiveBytes(nbytes))
    elif nbytes == 2:
      return struct.unpack(">h",self.receiveBytes(nbytes))
    elif nbytes == 3:
      pass #TODO: can' handle

    return struct.unpack(">i",self.receiveBytes(nbytes))

    return int.from_bytes(self.receiveBytes(nbytes), byteorder='big')

  def receiveFloat(self,length=4):
    return float(struct.unpack("f",self.receiveBytes(length))[0])

  def receiveString(self):
    mlen = self.receiveInt()
    s = self.receiveBytes(mlen)
    s = s.decode("utf-8")
    return s

#Class for streaming large JSON files
class JsonStreamLoader:
    # from jsonstreamer import JSONStreamer
    def __init__(self):
      self._json_streamer = JSONStreamer() #same for JSONStreamer
      self.partial_json   = None
      self.substructures  = []
      self.keys           = []
      # self._dicttype      = SortedDict
      # self._dicttype      = blist.sorteddict
      # self._dicttype      = blist.sorteddict
      self._dicttype      = dict
      self._json_streamer.auto_listen(self)

      self.review_n       = 0

    def substructure_assign(self,val):
      if isinstance(self.substructures[-1], self._dicttype):
        self.substructures[-1][self.keys.pop()] = val
      elif isinstance(self.substructures[-1], list):
        self.substructures[-1].append(val)

    def substructure_push(self,val):
      if len(self.substructures) == 0:
        self.partial_json = val
      else:
        self.substructure_assign(val)
      self.substructures.append(val)

    def _on_doc_start(self)       : pass
    def _on_doc_end(self)         : pass
    def _on_object_start(self)    : self.substructure_push(self._dicttype())
    def _on_array_start(self)     : self.substructure_push([])
    def _on_object_end(self)      :
      oldsub = self.substructures.pop()
      #If we're looking at a review
      if isinstance(oldsub, self._dicttype) and "appId" in oldsub:
        #Compress the object in memory
        oldsub = zlib.compress(pickle.dumps(oldsub))
        #Reassign the relevant part of the JSON
        self.partial_json["reviews"][self.review_n] = oldsub
        #Increment the review count
        self.review_n += 1
    def _on_array_end(self)       : self.substructures.pop()
    def _on_key(self,key)         : self.keys.append(key)
    def _on_value(self,value)     : self.substructure_assign(value)
    def _on_element(self,element) : self.substructure_assign(element)

    def parse(self, data):
      self._json_streamer.consume(data)
      return self.partial_json

    def parseFromIOHandle(self,inhandle,chunksize=None):
      if chunksize is None:
        # chunksize = 1024*1024*100 #100MB
        chunksize = 1024*1024 #1MB
        # chunksize = 1024*10#24 #1MB
      pos = 0
      while True:
        buf = inhandle.read(chunksize)
        if (buf == ''):
          break
        pos += chunksize
        print("\rRead {} MB".format(pos//1048576),end="")
        self.parse(buf)
        # print(self.partial_json["reviews"])
        # break
      print("")
      return self.partial_json

    def parseFromGzip(self,filename):
      inhandle = gzip.open(filename, 'rt', encoding='utf-8')
      loaded = self.parseFromIOHandle(inhandle)
      inhandle.close()
      return loaded

    def parseFromFile(self,filename):
      inhandle = open(filename, 'r', encoding='utf-8')
      loaded = self.parseFromIOHandle(inhandle)
      inhandle.close()
      return loaded
