from pymongo import mongo_client

class HealthcheckRepositoryMongo:

    def __init__(self, uri='127.0.0.1'):
        self._client = mongo_client.MongoClient(uri)
        self._db = self._client['healthcheck']
        self._results_coll = self._db['results']

    def push_result(self, time: float, title: str, value, desc=None):
        doc = {'time': time, 'title': title, 'value': value, "desc": desc}
        self._results_coll.insert_one(doc)

    def get_results(self, start_time: int, title: str):
        query = {'time': {'$gte': start_time}, 'title': title}
        cursor = self._results_coll.find(query, {'_id': 0})
        return list(cursor)
