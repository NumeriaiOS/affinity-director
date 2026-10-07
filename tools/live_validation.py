#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.services.qloo import QlooClient,QlooError
from app.services.orchestrator import execute_agent

def main()->int:
    if not os.getenv('QLOO_API_KEY','').strip():
        print('BLOCKED: QLOO_API_KEY is not configured; no live validation was attempted.')
        return 2
    client=QlooClient()
    scenarios=[
        {'name':'milan-cultural-night','signals':['Arctic Monkeys','A24','technical streetwear'],'location':'Milan'},
        {'name':'cross-domain-minimal','signals':['A24','Japanese contemporary design'],'location':None},
    ]
    reports=[]
    try:
        for scenario in scenarios:
            result=execute_agent(client,signals=scenario['signals'],location=scenario['location'],take=3,mode='live_validation')
            domains=sorted({item.get('domain') for item in result.get('items',[]) if item.get('domain')})
            graph=result.get('graph') or {}
            reports.append({'name':scenario['name'],'item_count':len(result.get('items',[])),'domains':domains,'evidence_coverage':graph.get('evidence_coverage',0.0),'pass':len(domains)>=3 and len(result.get('items',[]))>=4})
    except QlooError as exc:
        print('LIVE VALIDATION FAILED:',exc)
        return 1
    payload={'mode':'real_qloo_live_validation','scenarios':reports,'all_pass':all(row['pass'] for row in reports)}
    output=ROOT/'reports'/'live_validation.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))
    return 0 if payload['all_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
