import os
from dotenv import load_dotenv
load_dotenv('.env')

import httpx
_orig_init = httpx.Client.__init__
def _new_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _new_init

from supabase import create_client
url=os.environ.get('SUPABASE_URL')
key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)
res = client.table('knowledge_embeddings').select('id').limit(1).execute()
print(res)
