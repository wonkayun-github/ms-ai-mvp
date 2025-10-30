from azure.search.documents import SearchClient
import inspect
print(inspect.signature(SearchClient.search))
