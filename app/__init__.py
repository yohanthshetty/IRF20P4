from flask import Flask, render_template, request
import urllib.request
import pandas as pd
import pymongo
from urllib.parse import quote
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import json

app = Flask(__name__, static_url_path='/static')

username = "ubcse"
pwd = "connect@123"
conn = MongoClient("mongodb+srv://"+username+":"+quote(pwd)+"@mongocluster.ccsq3.mongodb.net/tweetcorpus?retryWrites=true&w=majority")
db = conn.test

from app import views, indexer, etl

