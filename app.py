import os
import re
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
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

@app.route('/')
def index():
    return render_template('index.html')
    # return 'Server Works!'

@app.route('/api/v1/in', methods=['GET'])
def get_recommendations():

    wiki_lang = request.args.get('lang')
    wiki_db = wiki_lang+"wiki"
    page_title = request.args.get('title')
    langs_translate = request.args.get('ltrans')
    if langs_translate!=None and isinstance(langs_translate,str):
        langs_translate = langs_translate.split("|")
    list_links = utils.link_translate_inlink(page_title, wiki_db, langs_translate=langs_translate)
    df = pd.DataFrame(list_links)
    if len(df)>0:
        df_formatted = df.groupby(by="source", as_index=False).agg(list)
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
            "results": results
        }
        return jsonify(out_json)
    else:
        return jsonify({'Error':"No results"})

if __name__ == '__main__':
    '''
    '''
    app.run(host='0.0.0.0')
