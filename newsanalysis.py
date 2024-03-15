import requests
import json
from datetime import date
from newsapi import NewsApiClient

def get_newsapi(newsapi_key, query, date_current, date_beginning):
    newsapi = NewsApiClient(api_key=newsapi_key)
    newsapi_articles_everything = newsapi.get_everything(q = query, from_param = date_current, to = date_beginning, language = "en", sort_by = "relevancy")
    return newsapi_articles_everything

def get_sentiment(text):
    endpoint = "https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/a6558b36-9b99-4d89-9ba7-2a030a4beda8/v1/analyze"

    username = "apikey"
    password = "hcFgR91LQxN1khLw58HiDgIcHzqUvedUX50Jmd9Tr71N"

    parameters = {'features': 'sentiment',
                  'version' : '2022-04-07',
                  'text' : text,
                  'language' : 'en'}
    
    resp = requests.get(endpoint, params = parameters, auth=(username, password))
    return resp.json()

def get_article_content(articles):
    contents = {}
    for article in articles['articles']:
        contents = {
            'title' : article['title'], 
            'content' : article['content']
            }
    return contents

def analyze_content(contents):
    analysis = []
    for content in contents:
        analysis.append(get_sentiment(content['content']))
    #analysis.append(get_sentiment(contents[0]))
    return analysis

def news_sentiment_score(analysis):
    totals = {
        "negative" : {"score" : 0, "count" : 0},
        "neutral" : {"score" : 0, "count" : 0},
        "positive" : {"score" : 0, "count" : 0},
    }

    for item in analysis:
        sentiment = item['sentiment']['document']['label']
        score = item['sentiment']['document']['score']
        totals[sentiment]['score'] += score
        totals[sentiment]['count'] +=1

    averages = {sentiment: totals[sentiment]["score"] / totals[sentiment]["count"] for sentiment in totals if totals[sentiment]["count"] > 0}
    return averages

date_current = str(date.today())
print(date_current)
date_beginning = "2023-12-31"

# News API
newsapi_key = "659142bd035e4a0e83a3a20737370f17"
newsapi_query = "Warner Music Group"

articles = get_newsapi(newsapi_key, newsapi_query, date_current, date_beginning)

contents = get_article_content(articles)

analysis = analyze_content(contents)

sentiment_score = news_sentiment_score(analysis)

print(sentiment_score)

# Next steps: build an AWS SQL server to upload the daily news of all these companies every time it gets queried to build up a database of news information and sentiment analysis 
# whose correlation with market prices can be back tested and implemented in a predictive model.