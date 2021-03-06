# Import libraries
import tweepy # Twitter
import numpy
import pandas
import matplotlib
from textblob import TextBlob, Word # Text pre-processing
import re # Regular expressions
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator # Word clouds
from PIL import Image
from pyspark.sql import SparkSession # Spark
import string
import nltk
nltk.download('wordnet')

# Import Twitter authentication file
from twitter_auth import *

# Twitter authentication
def twitter_auth():
    # This function has been completed for you
    # It uses hardcoded Twitter credentials and returns a request handler
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    return tweepy.API(auth)

# Retrieve Tweets
def get_tweets():
    # It creates a Tweet list and extracts Tweets
    account = 'AWSSupport'  # You can change this to any Twitter account you wish
    extractor = twitter_auth() # Twitter handler object
    tweets = []
    for tweet in tweepy.Cursor(extractor.user_timeline, id = account).items():
        tweets.append(tweet)
    print('Number of Tweets extracted: {}.\n'.format(len(tweets)))
    return tweets

# Create dataframe
def make_dataframe(tweets):
    # This function should return a dataframe containing the text in the Tweets
    return pandas.DataFrame(data = [tweet.text for tweet in tweets], columns = ['Tweets'])

# Pre-process Tweets
def clean_tweets(data):
    # It pre-processes the text in the Tweets and runs in parallel
    spark = SparkSession\
    .builder\
    .appName("PythonPi")\
    .getOrCreate()
    sc = spark.sparkContext
    paralleled = sc.parallelize(data)
    return paralleled.map(text_preprocess).collect()

# Pre-process text in Tweet
def text_preprocess(tweet):
    # This function should return a Tweet that consists of only lowercase characters,
    # no hyperlinks or symbols, and has been stemmed or lemmatized
    tweet = re.sub(r'https?:\/\/.*[\r\n]*', '', tweet)
    tweet = re.sub(r'#', '', tweet)
    tweet = re.sub(r'['+string.punctuation+']+', ' ', tweet)
    tweet = TextBlob(tweet).lower()
    tweet = Word(tweet)
    tweet = tweet.lemmatize()
    return str(tweet)

# Retrieve sentiment of Tweets
def generate_sentiment(data):
    # It returns the sentiment of the Tweets and runs in parallel
    spark = SparkSession\
    .builder\
    .appName("PythonPi")\
    .getOrCreate()
    sc = spark.sparkContext
    paralleled = sc.parallelize(data)
    return paralleled.map(data_sentiment).collect()

# Retrieve sentiment of Tweet
def data_sentiment(tweet):
    # This function should return 1, 0, or -1 depending on the value of text.sentiment.polarity
    text = TextBlob(str(tweet))
    if text.sentiment.polarity > 0:
        return 1
    elif text.sentiment.polarity == 0:
        return 0
    else:
        return -1

# Classify Tweets
def classify_tweets(data):
    # Given the cleaned Tweets and their sentiment,
    # this function should return a list of good, neutral, and bad Tweets
    good_tweets = ""
    neutral_tweets = ""
    bad_tweets = ""
    good_tweets = str(data[data['sentiment'] == 1]['cleaned_tweets'])
    neutral_tweets = str(data[data['sentiment'] == 0]['cleaned_tweets'])
    bad_tweets = str(data[data['sentiment'] == -1]['cleaned_tweets'])
    return [good_tweets, neutral_tweets, bad_tweets]

# Create word cloud
def create_word_cloud(classified_tweets) :
    good_tweets = classified_tweets[0]
    neutral_tweets = classified_tweets[1]
    bad_tweets = classified_tweets[2]
    stopwords = set(STOPWORDS)
    good_cloud = WordCloud(stopwords=stopwords).generate(good_tweets)
    neutral_cloud = WordCloud(stopwords=stopwords, colormap="gist_rainbow").generate(neutral_tweets)
    bad_cloud = WordCloud(stopwords=stopwords,colormap="magma").generate(bad_tweets)
    produce_plot(good_cloud, "Good.png")
    produce_plot(neutral_cloud, "Neutral.png")
    produce_plot(bad_cloud, "Bad.png")

# Produce plot
def produce_plot(cloud, name):
    matplotlib.pyplot.axis("off")
    matplotlib.pyplot.imshow(cloud, interpolation='bilinear')
    fig = matplotlib.pyplot.figure(1)
    fig.savefig(name)
    matplotlib.pyplot.clf()

#Retrieve Tweets
tweets = get_tweets()
#Create dataframe 
df = make_dataframe(tweets)
#Pre-process Tweets
df['cleaned_tweets'] = df['Tweets'].apply(text_preprocess)
#Retrieve sentiments
df['sentiment'] = df['cleaned_tweets'].apply(data_sentiment)
#Classify Tweets
classified_tweets = classify_tweets(df)
#Create Word Cloud
create_word_cloud(classified_tweets)
