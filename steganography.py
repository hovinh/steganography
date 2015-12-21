# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 18:10:14 2015
@author: hoxuanvinh
@facebook: https://www.facebook.com/vinh.hoxuan.9
@wordpress: https://hoxuanvinh.wordpress.com/
python version: 3.5
"""
# STEGANOGRAPHY + HARRY POTTER = Marauder's map
    
import nltk
import random
import bitarray
import string

def nextFirstWord(cprob_sam, word):
    for sample in cprob_sam[word].samples():
        return sample    
def nextTopWord(cprob_sam, word):
    candidateWords = []
    for sample in cprob_sam[word].samples():
        candidateWords.append((sample, cprob_sam[word].prob(sample)))
    candidateWords = sorted(candidateWords, key=lambda tup:tup[1])
    return candidateWords[0][0]
def nextRandomWord(cprob_sam, word):
    samples = []
    for sample in cprob_sam[word].samples():
        samples += [sample]
    return random.choice(samples)
def generateConditionWord(startWord, cprob_sam, numWord, nextWord):
    word = startWord
    count = numWord
    outputDoc = word[0].upper() + word[1:]
    while count > 0:
        count -= 1
        tmpWord = word
        word = nextWord(cprob_sam, word)
        if tmpWord == '.':
           outputDoc += ' ' + word[0].upper() + word[1:]
        else:
            outputDoc += ' ' + word
    # find a way to make stop make sense for reader. Continue until meet a punctuation
    while word not in string.punctuation:
        word = nextRandomWord(cprob_sam, word)
        outputDoc += ' ' + word
    return outputDoc

def nextStegaWord(cprob_sam, word, msgBits, index):
    candidateWords = []
    for sample in cprob_sam[word].samples():
        candidateWords.append((sample, cprob_sam[word].prob(sample)))
    candidateWords = sorted(candidateWords, key=lambda tup:tup[1], reverse = True)
    if len(candidateWords) >= 2:
        if msgBits[index] == True:
            return candidateWords[0][0], index+1
        else:
            return candidateWords[1][0], index+1
    return candidateWords[0][0], index
def generateStegaWord(startWord, cprob_sam, msgBits):
    word = startWord
    outputDoc = word[0].upper() + word[1:]
    index = 0 # for counting which bit is processed in msgBits
    while index < len(msgBits):
        word, index = nextStegaWord(cprob_sam, word, msgBits, index)
        outputDoc += ' ' + word
    # find a way to make stop make sense for reader. Continue until meet a punctuation
    outputDoc += '.\nMarauder\'s Map.'
    return outputDoc

def generateWord(corpusDir, resultDir, choice, startWord = None, message = None, numbWord = 100):
    print ('Loading corpus...')
    corpus, startWordList = readCorpus(corpusDir)
    print ('Finish loading.')
    print ('Processing...')
    
    # Preprocess start word list
    startWordList =set(startWordList)
    for punc in string.punctuation:
        if punc in startWordList:
            startWordList.remove(punc)
    print (startWordList)
    
    cfreq_sam = nltk.ConditionalFreqDist(nltk.bigrams(corpus))
    cprob_sam = nltk.ConditionalProbDist(cfreq_sam, nltk.MLEProbDist)
    random.seed(0)  # in case random, I want to make it deterministic      
    # Check if startWord exist in startWordList or not

    if startWord == None:
        startWord = random.choice(list(startWordList))
        
    if choice == 1: # generate first word in the list
        outputDoc = generateConditionWord(startWord, cprob_sam, numbWord, nextFirstWord)
    elif choice == 2: # generate the word has maximum probability
        outputDoc = generateConditionWord(startWord, cprob_sam, numbWord, nextTopWord)
    elif choice == 3: # generate random Words        
        outputDoc = generateConditionWord(startWord, cprob_sam, numbWord, nextRandomWord)
    elif choice == 4: # steganography
        ''' 
        the message is for english language, other should be checked 
        bitarray.fromstring() function
        '''
        if message == None:
            raise IOError("Do not enter message")
        msgBits = bitarray.bitarray()
        msgBits.fromstring(message)
        outputDoc = generateStegaWord(startWord, cprob_sam, msgBits)
    else:
        return False, None
    writeResult(resultDir, outputDoc)
    print ('Finish')
    return True, outputDoc
def extractBit(cprob_sam, curWord, nextWord):
    candidateWords = []
    for sample in cprob_sam[curWord].samples():
        candidateWords.append((sample, cprob_sam[curWord].prob(sample)))
    candidateWords = sorted(candidateWords, key=lambda tup:tup[1], reverse = True)
    if len(candidateWords) >= 2:
        if candidateWords[0][0] == nextWord:
            return '1'
        if candidateWords[1][0] == nextWord:
            return '0'
    return None
    
def extractMessage(cprob_sam, stegoDoc):
    msgBits = bitarray.bitarray()
    bit = extractBit(cprob_sam, stegoDoc[0].lower(), stegoDoc[1])
    if bit != None:
        msgBits.extend(bit)
    for i in range(1, len(stegoDoc)):
        bit = extractBit(cprob_sam, stegoDoc[i-1], stegoDoc[i])
        if bit != None:
            msgBits.extend(bit)
    return msgBits.tobytes()
        
def getMessage(corpusDir, stegoDir):
    print ('Loading corpus...')
    corpus, foo = readCorpus(corpusDir)
    print ('Finish loading.')
    print ('Loading stego doc...')
    stegoDoc, foo = readCorpus(stegoDir)
    stegoDoc = stegoDoc[:-6] # This is to determine the length of the true text that hide message
    print ('Finish loading.')
    print ('Processing...')     
    
    cfreq_sam = nltk.ConditionalFreqDist(nltk.bigrams(corpus))
    cprob_sam = nltk.ConditionalProbDist(cfreq_sam, nltk.MLEProbDist)
    print ('Extracted message:')
    message = extractMessage(cprob_sam, stegoDoc)
    print (message)
def readCorpus(fileName):
    # generate and count punctuation also as a token/word
    with open(fileName) as f:
        corpus = f.read().strip()
    tokenList = corpus.split()
    resultToken = []
    exceptWords = ['Mr.', 'Mrs.', 'wasn\'t', 'didn\'t', 'can\'t'] # the list of words you don't to strip the punctuation from the word
    punctuationList = string.punctuation 
    for token in tokenList:
        if token in exceptWords:
            resultToken.append(token)
        else:
            flag = False 
            token = token.replace('"', '')
            # This to ensure there is no word do not have following word
            for punc in punctuationList:
                if punc in token:
                    flag = True
                    token = token.replace(punc, ' '+punc+' ')
            if flag == True:
                token = token.split()
                for item in token:
                    resultToken.append(item)
            else:
                resultToken.append(token)
    startWordList = []
    tmpWord = '.'
    for word in resultToken:
        if tmpWord == '.':
            startWordList.append(word)
        tmpWord = word
    return resultToken, startWordList
def writeResult(fileName, outputDoc):
    with open(fileName, 'w') as f:
        f.write(outputDoc)

if __name__ == '__main__':
    flag, outputDoc = generateWord('b1-c01e.txt', 'result.txt', 1, 'the', 'Harry Potter')  
    '''
    if flag == False:
        print ('Something is wrong. Finish')
    # uncomment this part to extract message for choice = 4
    else:
        getMessage('E1.txt', 'result.txt')
    '''