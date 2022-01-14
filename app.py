import re
import requests
from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['JSON_SORT_KEYS'] = False
CUSTOM_UA = 'link recommendation orphans app -- mgerlach@wikimedia.org'

## load embedding
print("Try: http://127.0.0.1:5000/api/v1/in?wiki_db=simplewiki&title=Monument")

## download simple model via:
## wget https://analytics.wikimedia.org/published/datasets/one-off/mgerlach/linkrec/data/recs-link-translation_simplewiki.db

## locally: flask run

@app.route('/')
def index():
    return 'Server Works!'

@app.route('/api/v1/in', methods=['GET'])
def get_recommendations():

    wiki_db = request.args.get('wiki_db')
    page_title = request.args.get('title')
    item_id = title2qid(wiki_db,page_title)

    results = read_link_data(wiki_db, item_id)
    results_titles = recs_add_titles(results)

    # return jsonify(results)
    return jsonify(results_titles)
    # except:
    #     return jsonify({'Error':title})

def read_link_data(wiki_db, item_id):
    db_path = "recs-link-translation_simplewiki.db"
    conn = db.get_db(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM recs_in WHERE wiki_db='{0}' AND item_id='{1}'"
    results = cursor.execute(query.format(wiki_db,item_id)).fetchall()
    dict_results = {"wiki_db":wiki_db, "item_id":item_id}
    list_recs = []
    for r in results:
        dict_rec_r = {}
        item_id = r[1]
        item_id_rec = r[2]
        rank = r[3]
        n_exists = r[4]
        wiki_exists = eval(r[5])
        dict_rec_r["rank"] = rank
        dict_rec_r["link_qid"] = (item_id_rec,item_id)
        dict_rec_r["wikis_exist"] = wiki_exists
        list_recs+=[dict_rec_r]
    dict_results["recs"] = list_recs

    return dict_results

def title2qid(wiki_db,page_title):
    lang = wiki_db.replace("wiki","")
    page_title = page_title.replace(" ","_")

    headers = {"User-Agent": "linkrec: MGerlach_(WMF)"}
    api_url = "https://%s.wikipedia.org/w/api.php"%(lang)
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "pageprops",
        "format": "json",
    }
    response = requests.get( api_url,params=params, headers=headers).json()
    result = response['query']['pages']
    title,qid="",""
    for k,v in result.items():
        title = v.get("title","").replace(" ","_")
        qid = v.get("pageprops",{}).get("wikibase_item","")
        if title==page_title:
            break
    return qid

def recs_add_titles(recs):
    recs_formatted = {}
    wiki_db = recs.get("wiki_db")
    item_id = recs.get("item_id")

    recs_links = recs.get("recs")
    recs_links_formatted = []

    for ir,dict_r in enumerate(recs_links):

        qid_from, qid_to  = dict_r.get("link_qid")
        wikis_exist = dict_r.get("wikis_exist")
        wikis = [wiki_db] + wikis_exist

        headers = {"User-Agent": "linkrec: MGerlach_(WMF)"}
        api_url = "https://wikidata.org/w/api.php"
        params = {
            'action':'wbgetentities',
            'props':'sitelinks',
            'sitefilter':"|".join(wikis),
            'format' : 'json',
            'ids':qid_from+"|"+qid_to,
        }

        response = requests.get( api_url,params=params, headers=headers).json()
        result = response["entities"]

        s_from = result[qid_from]["sitelinks"]
        s_to = result[qid_to]["sitelinks"]

        title_from = s_from.get(wiki_db,{}).get("title","").replace(" ","_")
        title_to = s_to.get(wiki_db,{}).get("title","").replace(" ","_")
        title = title_to
        dict_r["link_title"] = (title_from,title_to)
        dict_r.pop("wikis_exist")

        wikis_exist_titles = {}
        for w in wikis_exist:
            title_from = s_from.get(w,{}).get("title","").replace(" ","_")
            title_to = s_to.get(w,{}).get("title","").replace(" ","_")
            wikis_exist_titles[w] = (title_from,title_to)
        dict_r["link_exists"] = wikis_exist_titles
        recs_links_formatted+=[dict_r]
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
