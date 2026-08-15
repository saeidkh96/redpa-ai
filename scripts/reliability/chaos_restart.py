from __future__ import annotations
import argparse
import json
import time
import urllib.request


def call(url: str, *, method='GET', body=None):
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(url,method=method,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:
        return json.load(response)


def main() -> int:
    parser=argparse.ArgumentParser(description='Approval-gated chaos restart for a stateless RedPA service.')
    parser.add_argument('--service', default='redpa-backend')
    parser.add_argument('--ops-agent-url', default='http://localhost:8070')
    parser.add_argument('--approve', action='store_true')
    args=parser.parse_args()
    diagnosis=call(f'{args.ops_agent_url}/containers/{args.service}/diagnose')
    print(json.dumps(diagnosis,indent=2))
    if not args.approve:
        print('Dry run only. Pass --approve to restart the allowlisted stateless service.')
        return 0
    result=call(f'{args.ops_agent_url}/containers/{args.service}/restart',method='POST',body={'approved':True,'reason':'Approved V9 resilience validation restart'})
    print(json.dumps(result,indent=2)); time.sleep(3)
    verify=call(f'{args.ops_agent_url}/containers/{args.service}/diagnose')
    print(json.dumps(verify,indent=2))
    return 0 if verify.get('state')=='running' else 2

if __name__ == '__main__':
    raise SystemExit(main())
