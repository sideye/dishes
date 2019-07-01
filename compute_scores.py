import os
import json
from textblob import TextBlob
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.sentiment.util import *
import math
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

vader_analyzer = SentimentIntensityAnalyzer()
for file_path in tqdm(os.listdir('./extracted_dish_info/')):
    dishes = {}
    with open('./extracted_dish_info/{}'.format(file_path), "r+") as fp:
        inp = json.load(fp)
    
    rankings = {'dishes': [], 'dish_sent':[], 'overall_sent': [], 'rating':[], 'dish_pop':[]}

    # Part 0: clean out non excerpted dishes
    to_remove = []
    for dish in inp:
        if not inp[dish]:
            to_remove.append(dish)
    for item in to_remove:
        del inp[item]
    
    # Part 1: determine sentiment of each dish
    category_scores = {}
    for dish in inp:
        category_scores[dish] = {}
    
    for dish in inp:
        dish_sent_sum = 0 
        for review in inp[dish]:
            excerpts = review['excerpts']
            excerpt_weight = 1
            sent_sum = 0
            for excerpt in excerpts:
                vader_sent = vader_analyzer.polarity_scores(excerpt)
                text_blob_sent = TextBlob(excerpt).sentiment
                overall_sent = 0.15*vader_sent['neg'] + 0.15*vader_sent['pos'] + 0.25 * vader_sent['compound'] + 0.45 * text_blob_sent.polarity
                sent_sum += excerpt_weight * overall_sent
            review_sent = sent_sum / len(excerpts) * math.log(5+len(excerpts) - 1, 5)
            dish_sent_sum += review_sent
        dish_sent = dish_sent_sum / len(inp[dish])
        category_scores[dish]['dish_sentiment'] = dish_sent
        
        rankings['dishes'] = rankings['dishes'] + [dish]
        rankings['dish_sent'] = rankings['dish_sent'] + [dish_sent]
      
    # Part 2: determine overall sentiment
    for dish in inp: 
        overall_sent_sum = 0
        for review in inp[dish]:
            review_text = review['review']
            vader_sent = vader_analyzer.polarity_scores(review_text)
            text_blob_sent = TextBlob(review_text).sentiment
            overall_sent = 0.15*vader_sent['neg'] + 0.15*vader_sent['pos'] + 0.25 * vader_sent['compound'] + 0.45 * text_blob_sent.polarity
            overall_sent_sum += overall_sent
        overall_sent = overall_sent_sum / len(inp[dish])
        category_scores[dish]['overall_sentiment'] = overall_sent
        
        rankings['overall_sent'] = rankings['overall_sent'] + [overall_sent]
    
    # Part 3: rating
    for dish in inp:
        ratings = [r['rating'] for r in inp[dish]]
        category_scores[dish]['avg_rating'] = sum(ratings)/len(ratings)
        
        rankings['rating'] = rankings['rating'] + [sum(ratings)/len(ratings)]
    
    # Part 4: dish popularity
    for dish in inp:
        category_scores[dish]['dish_popularity'] = len(inp[dish])
        
        rankings['dish_pop'] = rankings['dish_pop'] + [len(inp[dish])]
    
    # Part 5: restaurant popularity
    restaurant_popularity = pd.read_json('./reviews/{}'.format(file_path), lines=True).shape[0]
    for dish in inp:
        category_scores[dish]['rest_popularity'] = math.log(restaurant_popularity,10)
    
    # COMBINE
    # For now: do dish ranking through ranks. Will be changed in V2 when comparing dishes across restaurants
    for key in rankings:
        if key != 'dishes':
            rankings[key] = pd.Series(rankings[key]).rank()
    output_rankings = []
    for dish_sent, overall_sent, rating, dish_pop in zip(rankings['dish_sent'], rankings['overall_sent'], rankings['rating'], rankings['dish_pop']):
        score = dish_sent * 0.5 + overall_sent * 0.1 + rating * 0.2 + dish_pop * 0.2
        output_rankings.append(score)
        
    output_rankings = pd.Series(output_rankings).rank()
    
    output = {}
    for dish in inp:
        output[dish] = {}
    for dish, score, sentiment in zip(rankings['dishes'], output_rankings, rankings['dish_sent']):
        output[dish]['overall_score'] = score
        output[dish]['sentiment_score'] = sentiment
            
    with open('./output/{}'.format(file_path), "w+") as output_file:
        json.dump(output, output_file)

    
# IDEA: BUILD NLP model based on review data solely. Train results col can be found in yelp review scores