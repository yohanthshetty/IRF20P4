from app import app,conn 
from .indexer import hit_solr, process_query,news_retrieval
from .etl import jsonToDF, influence_score, fetch_topics_db
import json
from flask import jsonify, request, render_template
import pandas as pd
import json
import itertools
import os

import pandas as pd
import urllib.request

search = {}
global start
global stop

@app.route("/")
def input():
    return render_template('input.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form
      #p_data = data.items()
      return render_template("results.html",result = result)

@app.route("/search", methods=['POST'])
def search_tweets():
    sentiment = []
    name = []
    lang = []
    country = []
    hashtags = []
    topic = []
    f_topic = []
    # query = "covid warriors"
    #req_data = request.get_json(force=True)
    #search['search'] = request.form.get('search')
    #print(search)
    #data = hit_solr(search)
    req_data = request.form
    # print(req_data)
    for key,value in req_data.items():
        if key[:9] == 'sentiment':
           sentiment.append(key[10:-1])
        elif key[:4] == 'name':
           name.append(key[5:-1])
        elif key[:4] == 'lang':
           lang.append(key[5:-1])
        elif key[:7] == 'country':
           country.append(key[8:-1])
        elif key == 'Hashtags':
            hashtags = req_data[key].split(",")
        elif key == 'topic':
            topic = req_data[key].split(",")
            for _ in topic:
                f_topic.append(int(_))
        else:
            search[key]=value
            
    if 'search2' in search.keys():
        if search['search2'] != '':
            search['search']=search['search2']
        
    if 'sort' in search.keys() and search['sort']!= '0':
        sort = search['sort']
    else:
        sort = 'influence_score'
    
    if 'topic' not in search.keys():
        f_topic.append(22)
        
        
    # print(search)  
    # print(f_topic)
    search['sentiment']=sentiment
    search['name']=name
    search['lang']=lang
    search['country']=country
    search['hashtags'] = hashtags
    
    
    temp_dict1 = {
        'sentiment': search['sentiment'],
        'hashtag': search['hashtags'],
        'country': search['country'],
        'poi': search['name'],
        'lang': search['lang']
    }
    temp_dict = {
        'search': search['search'],
        'filters': temp_dict1
    }

    data = hit_solr(temp_dict)
    news = news_retrieval(temp_dict['search'])
    #print(news)
    docs = data.read().decode('utf-8')
    fin_docs = json.loads(docs)
    numFound = fin_docs['response']['numFound']
    fin_dic = fin_docs['response']['docs']
    if len(fin_dic) != 0:
        tweets_df = jsonToDF(fin_dic)
        new_df = influence_score(tweets_df,sort)
        new_df = fetch_topics_db(new_df,f_topic)
        fin_dic = new_df.to_dict('records')
    
    poi_name = {}
    lang = {}
    country = {}
    hashtags = {}
    sentiment = {}
    covid_g = {}

    facet_fields = fin_docs['facet_counts']['facet_fields']
    for key in facet_fields.keys():
        temp = {facet_fields[key][i]: facet_fields[key][i + 1] for i in range(0, len(facet_fields[key]), 2)}
        #print(type(temp))
        if key == "poi_name": poi_name = temp
        if key == "lang": lang = temp
        if key == "country": country = temp
        if key == "hashtags": hashtags = temp
        if key == "sentiment": sentiment = temp
    # print('***************************** VIEW BEFORE FINAL **************')
    
    list1 = []
    list2 = []
    for key,value in poi_name.items():
        list1.append(key)
        list2.append(value)
    chart_n = {
        'poi_names': list1,
        'counts': list2
    }

    list1 = []
    list2 = []
    for key,value in lang.items():
        list1.append(key)
        list2.append(value)
    chart_l = {
        'lang': list1,
        'counts': list2
    }

    list1 = []
    list2 = []
    for key,value in country.items():
        list1.append(key)
        list2.append(value)
    chart_c={
        'country': list1,
        'counts': list2
    }

    list1 = []
    list2 = []
    for key,value in sentiment.items():
        list1.append(key)
        list2.append(value)
    chart_s={
        'sentiment': list1,
        'counts': list2
    }

    list1 = []
    list2 = []
    for key,value in hashtags.items():
        list1.append(key)
        list2.append(value)
    chart_h={
        'hashtags': list1,
        'counts': list2
    }
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "static", "22.json")
    covid_g = json.load(open(json_url))
    
    final_result = {}
    final_result = {
        'news': news,
        'tweets': fin_dic,
        'analysis': {
            'poi_name': poi_name,
            'lang': lang,
            'country': country,
            'hashtags': hashtags,
            'sentiment': sentiment},
        'charts':{'hashtags':chart_h,'name':chart_n,'sentiment':chart_s,'lang':chart_l,'country':chart_c},
        'covid': covid_g,
        'total': numFound
    }
    #print(final_result['charts']['name']['count'])
    result = final_result
    temp11 = []
    result['total_pg'] = int(len(final_result['tweets'])/10)
    #print(final_result['tweets'])
    ################################# PAGINATION COMMENT #################################
    
    if 'pg_no' in search and 'stop' in search and 'start' in search: 
        search['start'] = 0+(10*(int(search['pg_no'])-1))
        search['stop'] = 9+(10*(int(search['pg_no'])-1))
    else:
        search['start'] = 0
        search['stop'] = 9 
    ######################################################################################


    for tweet in itertools.islice(final_result['tweets'],search['start'],search['stop']):
        temp11.append(tweet)
    #print(temp11)
    #print(len(temp11))
    result['tweets'] = temp11
    #result = final_result
    #print(result['tweets'])
    '''for key, value in result['analysis']:
        print(key)
        print(value)'''
    # print('***************************** VIEW BEFORE RETURN **************')
    return render_template("base.html",result = result)