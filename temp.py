import os
import requests
import json

env = {}
with open('backend/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k] = v.strip('"\'')

key = env.get('SUPABASE_SERVICE_ROLE_KEY')
url = env.get('SUPABASE_URL') + '/rest/v1/rpc/get_policies' 


