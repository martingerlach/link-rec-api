import re
import requests
from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['JSON_SORT_KEYS'] = False
CUSTOM_UA = 'link recommendation orphans app -- mgerlach@wikimedia.org'

## load embedding
print("Try: http://127.0.0.1:5000/api/v1/linkrec?wiki_db=simplewiki&item_id=Q1001474")

## download simple model via:
## wget https://analytics.wikimedia.org/published/datasets/one-off/mgerlach/linkrec/data/recs-link-translation_simplewiki.db

@app.route('/')
def index():
    return 'Server Works!'

@app.route('/api/v1/linkrec', methods=['GET'])
def get_recommendations():

    wiki_db = request.args.get('wiki_db')
    item_id = request.args.get('item_id')

    results = read_link_data(wiki_db, item_id)

    return jsonify(results)
    # except:
    #     return jsonify({'Error':title})

def read_link_data(wiki_db, item_id):
    db_path = "recs-link-translation_simplewiki.db"
    conn = db.get_db(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM recs_in WHERE wiki_db='{0}' AND item_id='{1}'"
    results = cursor.execute(query.format(wiki_db,item_id)).fetchall()
    results_formatted = []
    for r in results:
        wiki_db = r[0]
        item_id = r[1]
        item_id_rec = r[2]
        i_rec = r[3]
        n_exists = r[4]
        wiki_exists = eval(r[5])
        dict_return = {
            "wiki_db":wiki_db,
            "item_id_to":item_id,
            "item_id_from":item_id_rec,
            "rank":i_rec,
            "n_exist":n_exists,
            "wikis_exist":wiki_exists
        }
        results_formatted+=[dict_return]

    return results_formatted

if __name__ == '__main__':
    '''
    '''
    app.run(host='0.0.0.0')
