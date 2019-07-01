# Dishes
Ever had the trouble of deciding what to get at a restaurant? Dishes scrapes Yelp's reviews, extracts references to dishes, and performs sentiment analysis to help you determine what's best at a restaurant.

## Project Roadmap
- More robust dish name extraction from reviews
    - Disregard adjectives/adverbs in dish names.
    - Add detection for references with just one character off, such as apostrophes, plurals, spelling errors, etc.
- Build a new sentiment analyzer model based on scraped review data, with the validation being rating score.
- Improve recommendation algorithm
    - Update rank order algorithm
- Add support for more cities (NYC, LA, Vancouver, Chicago)