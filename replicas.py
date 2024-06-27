import pymysql
# https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database
def make_connection(wiki_db, replica_type="analytics"):
    """Connects to a host and database of the same name.
    
    `replica_type` can be either "analytics" (default), or "web"."""
    assert replica_type == "web" or replica_type == "analytics"
    return pymysql.connect(
        host=f"{wiki_db}.{replica_type}.db.svc.wikimedia.cloud",
        read_default_file="~/replica.my.cnf",
        database=f"{wiki_db}_p",
        charset='utf8'
    )

def query(conn, query):
    """Execute a SQL query against the connection, and return **all** the results."""
    with conn.cursor() as cur:
        cur.execute(query)
        data = cur.fetchall()
        return data