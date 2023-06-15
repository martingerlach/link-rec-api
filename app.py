import re
import requests
import pandas as pd
from flask import Flask, request, jsonify, render_template
import utils

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['JSON_SORT_KEYS'] = False
CUSTOM_UA = 'link recommendation orphans app -- mgerlach@wikimedia.org'

## load embedding
print("Try: http://127.0.0.1:5000/api/v1/in?wiki_db=enwiki&title=Alcohol_Act_(Switzerland)")

## locally: flask run

@app.route('/')
def index():
    return 'Server Works!'

@app.route('/api/v1/in', methods=['GET'])
def get_recommendations():

    wiki_db = request.args.get('wiki_db')
    page_title = request.args.get('title')
    langs_translate = request.args.get('langs')
    if langs_translate!=None and isinstance(langs_translate,str):
        langs_translate = langs_translate.split("|")

    list_links = utils.link_translate_inlink(page_title, wiki_db, langs_translate=langs_translate)
    df = pd.DataFrame(list_links)
    df_formatted = df.groupby(by="source", as_index=False).agg(list)
    df_formatted["n"] = df_formatted.apply(lambda x: len(x["source_translate"]),axis=1)
    df_formatted=df_formatted.sort_values(by="n",ascending=False)


    df_formatted["links"] = df_formatted.apply(lambda x: [ {
        "wiki_db_translate":x["wiki_db_translate"][i],
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
    return jsonify(results)
    # except:
    #     return jsonify({'Error':title})





    recs_formatted = {
        "wiki_db":wiki_db,
        "item_id":item_id,
        "title":title,
        "recs":recs_links_formatted
    }
    return recs_formatted

if __name__ == '__main__':
    '''
    '''
    app.run(host='0.0.0.0')
