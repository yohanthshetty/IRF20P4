import numpy as np
import json
from app import conn, pd

# tfile = open("solr_local.json", 'r', encoding= 'utf-8')

def fetch_topics_db(tweets_df,t_filter=' '):
    tweet_ids_list = tweets_df['tweet_id'].tolist()
    # print(tweet_ids_list,'list of ids')
    #print("Code reached here b4 connection to DB")
    #connecting to database using conn(connection) object of mongodb
    db = conn.tweetcorpus
    #print("Code reached here b4 find")
    #fetching results from corpusCollection in corpusDB
    results = list(db.Tweet.find({"tweet_id" : {"$in" : tweet_ids_list}}))
    # print(tweet_ids_list,'list of results')
    #print("Code reached here b4 normalize")
    #creating dataframe of results sent by database
    tweets_topic_df = pd.json_normalize(results)
    # print(tweets_topic_df,'list of merged')
    
    #merging two dfs on tweetid
    merged_df = pd.merge(tweets_df, tweets_topic_df[['tweet_id','topic_text', 'dominant_topic', 'topic_keywords']], on='tweet_id',how='outer')
    # print(merged_df,'merged df')
    
    if t_filter[0] !=22: 
        # print('inside',type(t_filter[0]))
        merged_df = merged_df[merged_df['dominant_topic'].isin(t_filter)]
    # print(t_filter)
    # print(merged_df,'merged df last')
    return merged_df

def jsonToDF(tweets):
    tweets_list = []
    
    for t in tweets:
        t_dict={}
        t_dict['tweet_id']= t.get('id',"") 
        t_dict['user_name'] = t.get('user.name')[0]
        
        if t.get('user.screen_name'):
            t_dict['screen_name']= t.get('user.screen_name')[0]
        else:
            t_dict['screen_name']= ""
        
        if t.get('full_text'):
            t_dict['full_text']= t.get('full_text')[0]
        else:
            t_dict['full_text']= ""
            
        if t.get('tweet_text'):
            t_dict['tweet_text']=t.get('tweet_text')[0]
        else:
            t_dict['tweet_text']= ""
               
        if t.get('text_en'):
            t_dict['text_en']=t.get('text_en')[0]
        else:
            t_dict['text_en']= ""        
        
        t_dict['hashtags']=t.get('hashtags',"")
        
        if t.get('lang'):
            t_dict['tweet_lang']=t.get('lang')[0]
        else:
            t_dict['tweet_lang']=""
            
        if t.get('country'):
            t_dict['country']=t.get('country')[0]
        else:
            t_dict['country']=""
            
        if t.get('tweet_date'):
            t_dict['tweet_date']=str(t.get('tweet_date')[0])[0:10]
        else:
            t_dict['tweet_date']=""  
        
        if t.get('sentiment'):
            t_dict['sentiment']=t.get('sentiment')[0]
        else:
            t_dict['sentiment']="neutral"
            
        if t.get('user.followers_count'):
            t_dict['followers']=t.get('user.followers_count')[0]
        else:
            t_dict['followers']= 0
            
        if t.get('user.friends_count'):
            t_dict['friends']=t.get('user.friends_count')[0]
        else:
            t_dict['friends']= 1
            
        if t.get('user.favourites_count'):
            t_dict['fav_count']=t.get('user.favourites_count')[0]
        else:
            t_dict['fav_count']= 0
            
        if t.get('user.listed_count'):
            t_dict['listed_count']=t.get('user.listed_count')[0]
        else:
            t_dict['listed_count']= 0
            
        if t.get('retweet_count'):
            t_dict['retweet_count'] = t.get('retweet_count')[0]
        else:
            t_dict['retweet_count'] = 0
            
        if t.get('poi_id'):
            if t.get('poi_id')[0] != "":
                t_dict['is_poi'] = 1
            else:
                t_dict['is_poi'] = 0
        else:
            t_dict['is_poi'] = 0
        
        if t.get('user.verified'):
            if t.get('user.verified')[0] is True:
                t_dict['is_verified'] = 1
            else:
                t_dict['is_verified'] = 0
        else:
            t_dict['is_verified'] = 0
            
        if t_dict['friends'] == 0:
            t_dict['follow_ratio']=round(t_dict['followers']/1,4)
        else:
            t_dict['follow_ratio']=round(t_dict['followers']/t_dict['friends'],4)
        
        tweets_list.append(t_dict)
        
    #dataframe from the entire corpus
    tweet_df = pd.DataFrame(tweets_list) 
    return tweet_df

def facetsToDF(facets):
    poi_list = facets.get('poi_name')
    return 0

def influence_score(tweets_df,sort='influence_score'):
    
    tweets_df['bm25_rank']=tweets_df.index + 1
    tweets_df['retweet_rank'] = tweets_df["retweet_count"].rank(ascending=False)
    tweets_df['fav_rank'] = tweets_df["fav_count"].rank(ascending=False)
    tweets_df['listed_rank'] = tweets_df["listed_count"].rank(ascending=False)
    tweets_df['fratio_rank'] = tweets_df["follow_ratio"].rank(ascending=False)
    tweets_df['tweet_score'] = ((10* (1/(tweets_df['retweet_rank'])))+ (8* (1/tweets_df['fav_rank'])) + (4* (1/(tweets_df['bm25_rank']))))/22
    tweets_df['user_authority'] = ((5*tweets_df['is_poi'])+ (5*tweets_df['is_verified']) + (10* (1/tweets_df['fratio_rank'])) + (8* (1/tweets_df['listed_rank'])))/28
    tweets_df['influence_score'] = round((tweets_df['user_authority'] + tweets_df['tweet_score']),4)
    
    sorted_df = tweets_df.sort_values(sort, ascending = False)
    
    return sorted_df.head(120)