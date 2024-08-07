import os
import re
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from mwconstants import WIKIPEDIA_LANGUAGES
import yaml
import pickle
import utils
import pandas as pd

app = Flask(__name__)

__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, 'default_config.yaml'))))
try:
    app.config.update(
        yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))
except IOError:
    # It is ok if there is no local config file
    pass

# Enable CORS for API endpoints
#CORS(app, resources={'*': {'origins': '*'}})
CORS(app)

# app = Flask(__name__)
# app.config["DEBUG"] = True
# app.config['JSON_SORT_KEYS'] = False
# CUSTOM_UA = 'readability-api -- mgerlach@wikimedia.org'

print("Try: http://127.0.0.1:5000/api/v1/in?lang=en&title=Alcohol_Act_(Switzerland)&ltrans=de|fr")
print("Try: http://127.0.0.1:5000/api/v1/in?lang=en&title=Degersee&ltrans=de|fr")
print("Try: http://127.0.0.1:5000/api/v1/out?lang=en&title=Tiwanaku")
print("Try: http://127.0.0.1:5000/api/v1/out?lang=en&title=Tiwanaku&ltrans=ca|es|fr")


@app.route('/')
def index():
    return render_template('index.html',
                           page_title=set_title(), lang=set_lang())
    # return 'Server Works!'

@app.route('/readmore')
def readmore():
    return render_template('readmore.html',
                           page_title=set_title(), lang=set_lang())
    # return 'Server Works!'

@app.route('/api/v1/in', methods=['GET'])
def get_recommendations():

    wiki_lang = set_lang()
    wiki_db = wiki_lang+"wiki"
    page_title = set_title()
    langs_translate = request.args.get('ltrans')
    if langs_translate!=None and isinstance(langs_translate,str):
        langs_translate = langs_translate.split("|")
    dict_result =  utils.link_translate_inlink(page_title, wiki_db, langs_translate=langs_translate)
    list_links = dict_result["inlinks_recs"]
    page_title_inlinks = dict_result["inlinks_exist"]
    results = []
    df = pd.DataFrame(list_links)
    if len(df)>0:
        df_formatted = df.groupby(by="source", as_index=False).agg(list)
        # sort recs by number of wikis it already exists in (n)
        df_formatted["n"] = df_formatted.apply(lambda x: len(x["source_translate"]),axis=1)
        df_formatted=df_formatted.sort_values(by="n",ascending=False)


        df_formatted["links"] = df_formatted.apply(lambda x: [ {
            "lang_translate":x["lang_translate"][i],
            "link_translate":(x["source_translate"][i],x["target_translate"][i])
        } for i in range(len(x["target"]))] ,axis=1)
        df_formatted = df_formatted[["source","links","n"]].reset_index(drop=True)
        results = []
        for i in range(min([10,len(df_formatted)])):
            dict_out = {
                "source":df_formatted["source"].iloc[i],
                "n_links": int(df_formatted["n"].iloc[i]),
                "links": df_formatted["links"].iloc[i]
            }
            results+=[dict_out]
    out_json = {
        "page_title": page_title,
        "lang": wiki_lang,
        "article": "https://{0}.wikipedia.org/wiki/{1}".format(wiki_lang,page_title),
        "n_inlinks": len(page_title_inlinks),
        "results": results
    }
    return jsonify(out_json)
    # else:
    #     return jsonify({'Error':"No results"})

@app.route('/api/v1/out', methods=['GET'])
def get_recommendations_out():
    n_wikis_min = 1
    wiki_lang = set_lang()
    wiki_db = wiki_lang+"wiki"
    page_title = set_title()
    langs_translate = request.args.get('ltrans')
    if langs_translate!=None and isinstance(langs_translate,str):
        langs_translate = langs_translate.split("|")
    dict_result =  utils.link_translate_outlink(page_title, wiki_db, langs_translate=langs_translate)
    list_links = dict_result["outlinks_recs"]
    page_title_outlinks = dict_result["outlinks_exist"]

    ## aggregating across langs
    results = []
    df = pd.DataFrame(list_links)
    df_formatted=pd.DataFrame()
    if len(df)>0:
        df_formatted = df.groupby(by="target", as_index=False).agg(list)
        df_formatted["n"] = df_formatted.apply(lambda x: len(x["target_translate"]),axis=1)
        # sort recs by number of wikis in which link already exists
        df_formatted=df_formatted.sort_values(by="n",ascending=False)

        df_formatted["links"] = df_formatted.apply(lambda x: [ {
            "lang_translate":x["lang_translate"][i],
            "link_translate":(x["source_translate"][i],x["target_translate"][i])
        } for i in range(len(x["source"]))] ,axis=1)

        # keep only links that exist in at n_wiki_min other wikis in order to reduce the potential list
        df_formatted = df_formatted[df_formatted["n"]>=n_wikis_min]
    if len(df_formatted)>0:
        # get the kin of all recs
#         df_formatted["kin"] = df_formatted.apply(lambda x: len(utils.get_page_inlinks(x["target"], wiki_db, do_continue=False)),axis=1)
        list_pages = list(df_formatted["target"].values)
        df_kin = utils.get_pages_kin(list_pages, wiki_db)
        df_formatted = df_formatted.join(df_kin.set_index("target"), how="left", on="target")

        # sort first by kin, second by n_wikis
        df_formatted["x_sort"] = df_formatted["n"]/(1+df_formatted["kin"])
        df_formatted = df_formatted.sort_values(by=["x_sort"], ascending=[False])
        # df_formatted = df_formatted.sort_values(by=["kin","n"], ascending=[True,False])



        # keep only top-10 suggestions
        for i in range(min([10,len(df_formatted)])):
            dict_out = {
                "target":df_formatted["target"].iloc[i],
                "n_wikis": int(df_formatted["n"].iloc[i]),
                "kin": int(df_formatted["kin"].iloc[i]),
                "links": df_formatted["links"].iloc[i],
            }
            results+=[dict_out]

    out_json = {
        "page_title": page_title,
        "lang": wiki_lang,
        "article": "https://{0}.wikipedia.org/wiki/{1}".format(wiki_lang,page_title),
        "n_outlinks": len(page_title_outlinks),
        "results": results
    }
    return jsonify(out_json)

def set_lang():
    if 'lang' in request.args:
        lang = request.args['lang'].lower()
        if lang in WIKIPEDIA_LANGUAGES:
            return lang
    return None

def set_title():
    if 'page_title' in request.args:
        title = request.args['page_title']
    elif 'title' in request.args:
        title = request.args['title']
    else:
        title = None

    if title:
        title = title.replace('_', ' ').strip()
        try:
            title = title[0].capitalize() + title[1:]
        except IndexError:
            title = None
    return title

if __name__ == '__main__':
    '''
    '''
    app.run(host='0.0.0.0')
