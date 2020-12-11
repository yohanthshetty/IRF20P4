from newsapi import NewsApiClient
import datetime as dt
from app import app,conn
import urllib.request
from urllib.parse import quote
import os, requests, uuid

import re
import json

def news_retrieval(query):
    
    
    newsapi = NewsApiClient(api_key = '3d243c5f6be449f089c8f6b75b98b6ff')
    data = newsapi.get_everything(q= query,from_param='2020-12-01',language='en', sort_by='relevancy', page = 1, page_size=20)
    all_articles = data['articles']
    
    results = []
    for article in all_articles:
        news_dict = {}
        news_dict['source'] = article.get('source').get('name')
        news_dict['title'] = article.get('title')
        news_dict['url'] = article.get('url')
        news_dict['urlToImage'] = article.get('urlToImage')
        news_dict['author'] = article.get('author')
        news_dict['publishedAt'] = str(dt.datetime.strptime(article.get('publishedAt'), "%Y-%m-%dT%H:%M:%SZ").date())
        if article.get('content') is not None:
            content = article.get('content')
            news_dict['content'] = article.get('content')[:-15]
        else:
            news_dict['content'] = " "
        results.append(news_dict)
        print(news_dict['url'])
    return results
    

# def translate_query(query):
#     subscription_key = "00d153d5f06546d3a11aaa8c5a14206c"
#     endpoint = "https://api.cognitive.microsofttranslator.com/"
#     path = '/translate?api-version=3.0'
#     params = '&to=en&to=hi&to=it'
#     api_url = endpoint + path + params

#     headers = {
#         'Ocp-Apim-Subscription-Key': subscription_key,
#         'Content-type': 'application/json',
#         'X-ClientTraceId': str(uuid.uuid4())
#     }
#     body = [{
#         'text': query
#     }]

#     request = requests.post(api_url, headers=headers, json=body)
#     response = request.json()
#     translated_text = {}
#     translated_text['lang'] = response[0]['detectedLanguage']['language']
#     for i in range(3):
#         translated_text[response[0]['translations'][i]['to']] = response[0]['translations'][i]['text']
#     return translated_text

def process_query(query):
    query = query.replace(r"\n", " ")
    query = query.replace(":", r"\:")
    query = "(" + query + ")"
    query = quote(query)
    return query

def process_filter(filter):
    new_filter = ""
    for f in filter:
        new_filter += f + " "
    new_filter = new_filter.strip()
    new_filter = new_filter.replace("\n", " ")
    new_filter = new_filter.replace(":", r"\:")
    new_filter = "(" + new_filter + ")"
    new_filter = quote(new_filter)
    return new_filter

def hit_solr(req_data):
    
    core_name = "IRF20P4"
    # core_name = "gettingstarted"
    ip_address = "http://54.236.232.142:8983/solr/"
    #ip_address = "http://localhost:8983/solr/"
    select_ = "/select?"
    or_string = "%20OR%20"
    and_string = "%20AND%20"
 
    
    
    # For testing
    # request
    # {
    #     "search": "coronavirus", 
    #     "filters": {
    #         "lang": "en" or "hi" or "it", 
    #         "country": "USA" or "India" or "Italy"], 
    #         "poi": ["joebiden","realdonaldtrump", "pmoindia"],
    #         "hashtag": ["TrumpVirus","COVID19"],
    #     }
    # }
    '''t_data = req_data'''
    
    '''for key,value in t_data:
        if key == 'search':
            query = value'''
            
    #print('******************* WORKS*********************')
    #print(req_data['search'])
    #for key, value in req_data:
    #    if key=='search':
    #        print(key, value)
    #        query = value
    #        break
    query = req_data['search']
    filters = req_data['filters']
    # print(req_data['filters'])
    hashtags = []
    country = []
    poi = []
    langu = []
    if filters:
        # filters = json.loads(filters)
        hashtags = filters.get('hashtag', None)
        country = filters.get('country', None)
        poi = filters.get('poi', None)
        langu = filters.get('lang', None)
        sentiment = filters.get('sentiment', None)

    query_hashtag = process_filter(hashtags) if hashtags else None
    query_country = process_filter(country) if country else None
    query_poi = process_filter(poi) if poi else None
    query_langu = process_filter(langu) if langu else None
    query_sentiment = process_filter(sentiment) if sentiment else None

    text_hashtags = re.findall(r"#(\w+)", query)
    text_hashtags = str(text_hashtags)
    text_hashtags = text_hashtags.replace('[','')
    text_hashtags = text_hashtags.replace(']','')
    text_hashtags = quote(text_hashtags)
    
    # Query Translation part below
    # translated_query = translate_query(query)
    # query_en = translated_query['en']
    # query_hi = translated_query['hi']
    # query_it = translated_query['it']

# delete below 3 lines
    query_en = query
    query_hi = query
    query_it = query

    query_en = process_query(query_en)
    query_hi = process_query(query_hi)
    query_it = process_query(query_it)

    # querylang = translated_query['lang']
# delete below line
    querylang = 'en'

    highlight_search = "&hl.fl=full_text,text_*&hl=on&hl.simple.pre=%3Cspan%20class%3D%22tweet-hl%22%3E&hl.simple.post=%3C%2Fspan%3E"
    if text_hashtags == "":
        query_parser = "&defType=edismax&qf=hashtags%5E1.2%20"
    else:
        query_parser = "&defType=edismax&qf="
    facet_search = "&facet.field=poi_name&facet.field=lang&facet.field=country&facet.field=hashtags&facet.field=sentiment&facet.limit=4&facet=on&facet.mincount=1"
    stopwords = "&stopwords=true"

    # select_fields = "fl=" + process_query("id, country, user.screen_name, full_text, tweet_text, tweet_lang, tweet_date, score")
    select_fields = "&fl=*"
    limit = "&indent=true&rows=500&wt=json"
    if text_hashtags == "":
        first_inurl = select_fields + "&q=%28" + 'text_en' + '%3A%20' + query_en + or_string + 'text_it' + '%3A%20' + query_it + or_string + 'text_hi' + '%3A%20' + query_hi + "%29"
    else:
        first_inurl = select_fields + "&q=%28" + "hashtags" + '%3A%20' + text_hashtags + or_string + 'text_en' + '%3A%20' + query_en + or_string + 'text_it' + '%3A%20' + query_it + or_string + 'text_hi' + '%3A%20' + query_hi + "%29"
    first_inurl = ip_address + core_name + select_ + first_inurl
    temp_array = []
    temp_flag = False


    if hashtags:
        temp_array.append("hashtags:" + query_hashtag)
        temp_flag = True
    if country:
        temp_array.append("country:" + query_country)
        temp_flag = True
    if poi:
        temp_array.append("poi_name:" + query_poi)
        temp_flag = True
    if langu:
        temp_array.append("lang:" + query_langu)
        temp_flag = True
    if sentiment:
        temp_array.append("sentiment:" + query_sentiment)
        temp_flag = True
     
    if querylang == 'hi':
        mid_inurl = "text_en%5E1.6%20text_hi%5E2.5%20text_it%5E2.0&tie=0.1"
    elif querylang == 'it':
        mid_inurl = "text_en%5E1.6%20text_hi%5E2.2%20text_it%5E2.7&tie=0.1"
    elif querylang == 'en':
        mid_inurl = "text_en%5E2.5%20text_hi%5E2.0%20text_it%5E2.0&tie=0.1"


    if temp_flag:
        inurl = first_inurl + and_string + and_string.join(temp_array)+ query_parser + mid_inurl + highlight_search + facet_search + limit

    else:
        inurl = first_inurl + query_parser + mid_inurl + highlight_search + facet_search + stopwords + limit
    # print(inurl)
    data = urllib.request.urlopen(inurl)
    # docs = data.read()
    # docs = docs.decode('utf-8')
    # fin_data = json.loads(docs)
    # numFound = fin_data['response']['numFound']
    # return fin_data['response']['docs'], numFound
    # print('***************************** INDEXER BEFORE END **************')
    return data

def hit_solr_news(search):
    core_name = "gettingstarted"
    # core_name = "news_articles_core"
    ip_address = "http://localhost:8983/solr/"
    select_ = "/select?"

    query = search

    # print(query)
    inurl = ip_address + core_name + select_ + 'q=' + process_query(query)    
    # print(inurl)
    data = urllib.request.urlopen(inurl)
    return data