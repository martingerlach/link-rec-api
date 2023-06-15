import requests
import math
import numpy as np


def get_page_langs(page_title, wiki_db):
    """
    find all languages in which a page exists.

    Returns [{{'wiki_db': WIKI_DB, 'page_title': PAGE_TITLE}]

    TODO: make it optional to only check some languages instead of all.
    """
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%( wiki_db.replace('wiki','') )

    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'langlinks',
        'format': 'json',
    }

    list_page_title_lang = []
    results = []
    try:
        response = requests.get( api_url_base,params=params, headers=headers).json()
        results = list(response["query"]["pages"].values())[0]["langlinks"]
    except:
        pass
    for r in results:
        r_out = {"wiki_db":r["lang"]+"wiki", "page_title":r["*"]}
        list_page_title_lang+=[r_out]
    return list_page_title_lang

def get_page_inlinks(page_title, wiki_db):
    """
    Get all inlinks for a given page (main namespace, non-redirects).

    Only returns first 500 results for now.

    TODO: use continue to also get results beyond 500
    """
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%( wiki_db.replace('wiki','') )

    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'linkshere',
        'lhprop': 'title',
        'lhnamespace': '0',
        'lhshow': '!redirect',
        'lhlimit': 500,
        'format': 'json',
    }
    page_title_inlinks = []
    try:
        response = requests.get( api_url_base,params=params, headers=headers).json()
        results = list(response["query"]["pages"].values())[0]["linkshere"]
        for s in results:
            page_title_inlinks += [s["title"].replace(" ","_")]
    except:
        pass
    return page_title_inlinks

def get_pages_lang(list_pages, wiki_db, wiki_db_translate, n_batch = 50):
    """
    Get page-titles from wiki_db in wiki_db_translate (if they exist)
    """
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%( wiki_db.replace('wiki','') )

    list_pages_translate = []
    ## splitting into batches (n_batch=50)
    list_pages_split = np.array_split(list_pages,math.ceil(len(list_pages)/n_batch))
    for list_pages_batch in list_pages_split:
        params = {
            'action': 'query',
            'titles': "|".join(list_pages_batch),
            'prop': 'langlinks',
            'lllang': '%s'%( wiki_db_translate.replace('wiki','') ),
            'lllimit': 500,
            'format': 'json',
        }
        # try:
        response = requests.get( api_url_base,params=params, headers=headers).json()
        results = [h for h in list(response["query"]["pages"].values()) if "langlinks" in h]

        for s in results:
            s_out = {
                "page_title":s["langlinks"][0]["*"],
                "page_title_original":s["title"],
                "wiki_db_original":wiki_db
            }
            list_pages_translate += [s_out]
        # except:
        #     pass
    return list_pages_translate

def link_translate_inlink(page_title, wiki_db, langs_translate=None):
    list_links = []

    # find the same article in other languages
    page_title_langs = get_page_langs(page_title, wiki_db)
    # find inlinks in each language and check if they exist in wiki_db
    for r in page_title_langs:
        p = r["page_title"]
        w = r["wiki_db"]
        # if we are only checking some languages
        if langs_translate != None:
            if isinstance(langs_translate,list):
                if w.replace("wiki","") not in langs_translate:
                    continue
        r_inlinks = get_page_inlinks(p,w)
        r_inlinks_translations = get_pages_lang(r_inlinks, w, wiki_db)
        for r_t in r_inlinks_translations:
            dict_out = {
                "source":r_t["page_title"],
                "target": page_title,
                "source_translate": r_t["page_title_original"],
                "target_translate": p,
                "wiki_db_translate": w,
            }
            list_links += [dict_out]
        # break
    return list_links