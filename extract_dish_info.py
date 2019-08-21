import pandas as pd
import os
import re
import string
import spacy
import json
from spacy.matcher import PhraseMatcher
from tqdm import tqdm

def clean_dish_names(dish):
    """Given a dish string, return the cleaned dish string by removing unnecessary white space and punctuation, and making everything lower case."""

    dish = re.sub(r"[\n\t]*", "", dish)
    dish = re.sub(r"  +", "", dish)
    dish = dish.translate(str.maketrans('', '', string.punctuation))
    dish = dish.lower()
    dish = re.sub(r"\d", "", dish)
    if not dish: # If nothing exists
        return ""
    dish = re.findall(r"(.+?)\s*$", dish)[0] # remove trailing whitesapce
    return dish

def get_dish_names_from_match(matches, doc):
    """Determine which dishes are mentioned given a match."""
    dishes_for_cache = []
    for match, start, stop in matches:
        dish_name = doc[start:stop].text.lower()
        if dish_name not in dishes_for_cache:
            dishes_for_cache.append(dish_name)
    return dishes_for_cache

def dump_cache(cache, dishes_for_cache, author):
    """Empty the cache and store the cached sentences into the dish's excerpts for future sentiment analysis. 
    A cache essentially holds the most recent consecutive sentences that are assumed to describe a dish."""
    if cache:
        for d in dishes_for_cache:
            if phrases[d] and phrases[d][-1]['author'] == author:
                phrases[d][-1]['excerpts'] += cache
            else:
                phrases[d].append({'excerpts': cache, 'author': author})

nlp = spacy.load("en_core_web_sm")
menu_item_list = [path for path in os.listdir('./menu_items/') if not path.startswith(".")] # to remove hidden OS files
for restaurant_path in tqdm(menu_item_list): 
    restaurant_name = restaurant_path[:-4] # Strips the .txt part of the path

    # Extract dish names
    with open("menu_items/{}.txt".format(restaurant_name)) as file:
        dishes = file.readlines()
    dishes = [clean_dish_names(dish) for dish in dishes if clean_dish_names(dish)]
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER") # Matches on dish names
    dishes_doc = [nlp.make_doc(dish) for dish in dishes]
    matcher.add("Dishes", None, *dishes_doc) 

    # Get table of reviews
    reviews_table = pd.read_json("reviews/{}.json".format(restaurant_name), lines = True)
    reviews_table.reviewRating = reviews_table.reviewRating.apply(lambda d: d['ratingValue'])
    
    phrases = {}
    for dish in dishes:
        phrases[dish] = []
    for index, row in tqdm(reviews_table.iterrows()): # Iterate through all reviews
        """Go through each review by sentence. A sentence that contains a dish reference and its subsequent sentences before encountering another dish name or a new paragraph is assumed to be about the referenced dish.
        Subsequent sentences are downweighted logarithmically in terms of relevance."""
        review = row.description
        date = row.datePublished
        rating = row.reviewRating
        author = row.author
        doc = nlp(review)
        dishes_for_cache = []
        dishes_mentioned = set()
        cache = []
        for sentence in doc.sents: # Iterate over each sentence in the review
            sentence_doc = sentence.as_doc()
            matches = matcher(sentence_doc) 
            if matches or "\n\n" in sentence.text: # Dump cache because either paragraph has ended or a new dish is referenced.
                dump_cache(cache, dishes_for_cache, author)
                if matches and "\n\n" in sentence.text:  # Dish name referenced in sentence and last line of paragraph.
                    dump_cache([sentence_doc.text], get_dish_names_from_match(matches, sentence_doc),author) # New mention
                    for d in get_dish_names_from_match(matches, sentence_doc):
                        dishes_mentioned.add(d)
                    cache = []
                    dishes_for_cache = []
                elif matches: # Dish name referenced in sentence
                    cache = [sentence_doc.text]
                    dishes_for_cache = get_dish_names_from_match(matches, sentence_doc)
                    for d in get_dish_names_from_match(matches, sentence_doc):
                        dishes_mentioned.add(d)
                elif "\n\n" in sentence.text: # Last line of paragraph
                    cache = []
                    dishes_for_cache = []
            else:
                cache.append(sentence_doc.text)
        dump_cache(cache, dishes_for_cache, author) 
        for d in dishes_mentioned:
            phrases[d][-1]['review'] = review
            phrases[d][-1]['rating'] = rating
            phrases[d][-1]['date'] = date
    
    with open('extracted_dish_info/{}.json'.format(restaurant_name), "w+") as file:
        json.dump(phrases, file)