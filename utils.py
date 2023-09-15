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
        'lllimit': 500,

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

def get_page_inlinks(page_title, wiki_db, do_continue = True):
    """
    Get all inlinks for a given page (main namespace, non-redirects).

    Retrieves all inlinks in batches of 500 using continue https://www.mediawiki.org/wiki/API:Continue
    if do_continue == False, we only get the first batch of 500 inlinks and wont use continue.

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
    last_continue = {}
    while True:
        params.update(last_continue)
        response = requests.get( api_url_base,params=params, headers=headers).json()
        results = list(response["query"]["pages"].values())[0].get("linkshere",[])
        for s in results:
            page_title_inlinks += [s["title"].replace(" ","_")]
        # if there is no continue then we got all results so we can stop
        if 'continue' not in response:
            break
        if do_continue == False:
            break
        # get the new continue parameter
        last_continue = response["continue"]
    return page_title_inlinks

def get_page_outlinks(page_title, wiki_db):
    """
    Get all outlinks for a given page (main namespace).

    Only returns first 500 results for now.

    """
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%( wiki_db.replace('wiki','') )

    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'links',
        # 'lhprop': 'title',
        'plnamespace': '0',
        # 'lhshow': '!redirect',
        'pllimit': 500,
        'format': 'json',
    }
    page_title_outlinks = []
    last_continue = {}
    while True:
        params.update(last_continue)
        response = requests.get( api_url_base,params=params, headers=headers).json()
        results = list(response["query"]["pages"].values())[0].get("links",[])
        for s in results:
            page_title_outlinks += [s["title"].replace(" ","_")]
        # if there is no continue then we got all results so we can stop
        if 'continue' not in response:
            break
        # get the new continue parameter
        last_continue = response["continue"]
    # resolve redirects
    page_title_outlinks_resolved = resolve_redirects_titles(page_title_outlinks,wiki_db)
    return page_title_outlinks_resolved

def resolve_redirects_titles(list_pages, wiki_db, n_batch = 50):
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%(  wiki_db.replace('wiki','') )

    list_pages_resolved = []
    if len(list_pages) > 0:
        ## splitting into batches (n_batch=50)
        list_pages_split = np.array_split(list_pages,math.ceil(len(list_pages)/n_batch))
        for list_pages_batch in list_pages_split:
            params = {
                'action': 'query',
                'titles': "|".join(list_pages_batch),
                'redirects': "True",
                'formatversion': "2",
                'format': 'json',
            }
            try:
                response = requests.get( api_url_base,params=params, headers=headers).json()
                results = response["query"]["pages"]
                for page in results:
                    title = page["title"].replace(" ","_")
                    list_pages_resolved += [title]
            except:
                pass
    return sorted(list(set(list_pages_resolved)))

def get_pages_lang(list_pages, wiki_db, wiki_db_translate, n_batch = 50):
    """
    Get page-titles from wiki_db in wiki_db_translate (if they exist)
    """
    headers = {"User-Agent": "MGerlach_(WMF) WMF-Research"}
    api_url_base = 'https://%s.wikipedia.org/w/api.php'%( wiki_db.replace('wiki','') )

    list_pages_translate = []
    if len(list_pages) > 0:
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
            try:
                response = requests.get( api_url_base,params=params, headers=headers).json()
                results = [h for h in list(response["query"]["pages"].values()) if "langlinks" in h]

                for s in results:
                    s_out = {
                        "page_title":s["langlinks"][0]["*"],
                        "page_title_original":s["title"],
                        "wiki_db_original":wiki_db
                    }
                    list_pages_translate += [s_out]
            except:
                pass
    return list_pages_translate

def link_translate_inlink(page_title, wiki_db, langs_translate=None):
    list_links = []

    # find the same article in other languages
    page_title_langs = get_page_langs(page_title, wiki_db)
    # find existing inlinks
    page_title_inlinks = get_page_inlinks(page_title, wiki_db)
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
            # remove if the translated inlink already exists
            if r_t["page_title"].replace(" ","_") in page_title_inlinks:
                continue
            dict_out = {
                "source":r_t["page_title"],
                "target": page_title,
                "source_translate": r_t["page_title_original"],
                "target_translate": p,
                "lang_translate": w.replace("wiki",""),
            }
            list_links += [dict_out]
        # break
    dict_out = {
        "inlinks_exist": page_title_inlinks,
        "inlinks_recs": list_links
    }
    return dict_out

def link_translate_outlink(page_title, wiki_db, langs_translate=None):
    list_links = []

    # find the same article in other languages
    page_title_langs = get_page_langs(page_title, wiki_db)
    # find existing inlinks
    page_title_outlinks = get_page_outlinks(page_title, wiki_db)
    # find inlinks in each language and check if they exist in wiki_db
    for r in page_title_langs:
        p = r["page_title"]
        w = r["wiki_db"]
        # if we are only checking some languages
        if langs_translate != None:
            if isinstance(langs_translate,list):
                if w.replace("wiki","") not in langs_translate:
                    continue
        r_outlinks = get_page_outlinks(p,w)
        r_outlinks_translations = get_pages_lang(r_outlinks, w, wiki_db)
        for r_t in r_outlinks_translations:
            # remove if the translated inlink already exists
            if r_t["page_title"].replace(" ","_") in page_title_outlinks:
                continue
            dict_out = {
                "source":page_title,
                "target":r_t["page_title"],
                "source_translate": p,
                "target_translate": r_t["page_title_original"],
                "lang_translate": w.replace("wiki",""),
            }
            list_links += [dict_out]
        # break
    dict_out = {
        "outlinks_exist": page_title_outlinks,
        "outlinks_recs": list_links
    }
    return dict_out