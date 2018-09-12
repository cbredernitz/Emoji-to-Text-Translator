from gensim.models import Word2Vec
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
import os,sys,re,csv
import string
import numpy as np
from nltk.translate.bleu_score import sentence_bleu

#spyacy is a very good and fast parser to use to give some context and structure to the landuage model.  Example would be to use this and the word2vec.  We would use this to make a large matrix with, example: 80% Word2Vec and 20% selectional preferences.

stop_words = set(stopwords.words('english'))
#...............................................................................
def load_and_tokenize(filename):
	"""Loading and tokenizing our file into a
		list of lists to pass into Gensim."""
	global stop_words
	tkizr = TweetTokenizer(strip_handles=True, reduce_len=True)
	f = open(filename, 'r', encoding = 'UTF-8', errors = "replace")
	full_lst = []
	punctuation = """!"$%&'()*+,-./:;<=>?[\]^_`{|}~"""
	print("-- Loading and tokenizing the file --")
	for line in f.readlines():
		lst = line.split('\t')[1]
		n_lst = [w.lower() for w in lst.split() if not w in stop_words and not w.startswith('#')]
		n_str = ' '.join(n_lst)
		table = str.maketrans({key: None for key in punctuation})
		n_str = n_str.translate(table)
		tokenized = tkizr.tokenize(n_str)
		full_lst.append(tokenized)
	print("-- Tokenization Compelted --")
	return full_lst

#...............................................................................
#  Loading the trained word2vec model
def load_model():
	"""Loading the trained word2vec model"""
	model = Word2Vec.load('tmp/completemodel')
	return model

def save_model(filename):
	"""Saving the trained word2vec model"""
	sentences = load_and_tokenize(filename)
	print("-- Training the Model --")
	model = Word2Vec(sentences, size=200, window=4, min_count=50, workers=4)
	model.train(sentences, total_examples=len(sentences), epochs=6)
	model.save('tmp/completemodel')
	print("-- Training Complete --")
	return model

#...............................................................................
def text_to_emoji(sentence):
	"""Translating a text sentence to emojis"""
	new_sentence = []
	words = sentence.split()
	for word in words:
		word = word.lower()
		if word in stop_words:
			new_sentence.append(word)
		else:
			try:
				for idx, x in enumerate(model.wv.most_similar(positive = word, topn = 1000)):
					try:
						x[0].encode('ISO 8859-1')
						if idx == 999:
							new_sentence.append(word)
						else:
							continue
					except:
						if x[1] <= 0.2:
							new_sentence.append(word)
							break
						else:
							new_sentence.append(x[0])
							break
			except KeyError:
				new_sentence.append(word)
	return new_sentence

#...............................................................................
def emoji_to_text(sentence):
	"""Translating a sentence containing emojis into text"""
	new_sentence = []
	words = sentence.split()
	for word in words:
		word = word.lower()
		if word in stop_words:
			new_sentence.append(word)
		else:
			try:
				for x in model.wv.most_similar(positive = word, topn = 1000):
					try:
						x[0].encode('ISO 8859-1')
						if x[1] <= 0.2:
							new_sentence.append(word)
							break
						else:
							new_sentence.append(x[0])
							break
					except:
						continue
			except KeyError:
				new_sentence.append(word)
	return new_sentence

#...............................................................................
if __name__ == '__main__':
	if sys.argv[1] == "--doc":
		filename = sys.argv[2]
		model = save_model(filename)

# The below was used to make the "Let it Go" txt file with our results.
	# model = load_model()
	# with open("snowman.txt", 'r') as snow:
	# 	f = snow.read()
	# 	sent_list = text_to_emoji(f)
	# 	s = ""
	# 	for n in sent_list:
	# 		space = n + " "
	# 		s+= space
	# 	print(s)

	else:
		model = load_model()
		if sys.argv[1] == "--emoji":
			input_sentence = input("Please enter the sentence you want to be translated: ")
			sent_list = text_to_emoji(input_sentence)
			s = ""
			for n in sent_list:
				space = n + " "
				s+= space
			print(s)

		if sys.argv[1] == "--text":
			input_sentence = input("Please enter the sentence you want to be translated: ")
			sent_list = emoji_to_text(input_sentence)
			s = ""
			for n in sent_list:
				space = n + " "
				s+= space
			print(s)

		if sys.argv[1] == "--BLEU_emoji":
			sent_scores = []
			orig_and_ml = []
			fopen = open("annotated_tweets_text-emoji.tsv", encoding='utf-8')
			for each in fopen.readlines():
				annotated_reference = each.split('\t')[1]
				reference = annotated_reference.split()
				orig_tweet = each.split('\t')[0]
				candidate = text_to_emoji(orig_tweet)
				score = sentence_bleu(reference, candidate)
				sent_scores.append(score)
				candidate_string = ' '.join(candidate)
				orig_and_ml.append((annotated_reference, candidate_string, score))
			fopen.close()
			print(len(sent_scores))
			print("Individual Sentence BLEU Scores:")
			print(sent_scores)
			print("-"*20)
			print("Mean Sentence BLEU Score: \n" + str(np.mean(sent_scores)))
			with open("text_to_emoji_results.txt", 'w') as text_to_e:
				for info in orig_and_ml:
					text_to_e.write(str(info[0].rstrip())+'\t'+str(info[1])+'\t'+str(info[2])+'\n')
				text_to_e.write("\n Mean Sentence BLEU Score: " + str(np.mean(sent_scores)))
				text_to_e.close()

		if sys.argv[1] == "--BLEU_text":
			sent_scores = []
			orig_and_ml = []
			fopen = open("annotated_emoji_to_text.tsv", encoding='utf-8')
			for each in fopen.readlines():
				annotated_reference = each.split('\t')[1]
				reference = annotated_reference.split()
				orig_tweet = each.split('\t')[0]
				candidate = emoji_to_text(orig_tweet)
				score = sentence_bleu(reference, candidate)
				sent_scores.append(score)
				candidate_string = ' '.join(candidate)
				orig_and_ml.append((annotated_reference, candidate_string, score))
			fopen.close()
			print(len(sent_scores))
			print("Individual Sentence BLEU Scores:")
			print(sent_scores)
			print("-"*20)
			print("Mean Sentence BLEU Score: \n" + str(np.mean(sent_scores)))
			with open("emoji_to_text_results.txt", 'w') as e_to_text:
				for info in orig_and_ml:
					e_to_text.write(str(info[0].rstrip())+'\t'+str(info[1])+'\t'+str(info[2])+'\n')
				e_to_text.write("\n Mean Sentence BLEU Score: " + str(np.mean(sent_scores)))
				e_to_text.close()

		if sys.argv[1] == "--BLEU_song":
			annotopen = open("annotate_snowman.txt", 'r', encoding='utf-8')
			resultopen = open("snowman_word2vec.txt", 'r', encoding='utf-8')
			annoread = annotopen.read()
			resultread = resultopen.read()
			annlist = annoread.split()
			resultlist = resultread.split()
			score = sentence_bleu(annlist, resultlist)
			print(score)
