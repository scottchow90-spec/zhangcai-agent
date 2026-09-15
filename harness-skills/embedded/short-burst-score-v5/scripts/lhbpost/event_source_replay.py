"""Recheck bounded announcement requests, payloads and reviewed source documents.

Only the reviewed neutral document mappings below are supported. New documents
require a separate content review; a supplied success/review boolean never adds
a new mapping. Historical collection timestamps are preserved as captured.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TZ=timezone(timedelta(hours=8))
CNINFO='https://www.cninfo.com.cn/new/hisAnnouncement/query'
EASTMONEY='https://np-anotice-stock.eastmoney.com/api/security/ann'
PUBLICATION_BASIS='display_time (not notice_date or announcementTime)'
APPROVED_DOCUMENTS={
    '1225560326':{'code':'600207.SH','sha256':'a1f5c9b9787a76231be710119ae6bf1854ab25f5139087bdf7435fcde4e012dc','type':'asset_sale_related_party_intention','pages':5,
        'title':'安彩高科关于筹划资产出售暨关联交易的提示性公告'},
    '1225556856':{'code':'605058.SH','sha256':'010f91e24b95bf85f5bb318d885c4b4367120e0853349329ef1698161ccf952b','type':'equity_incentive_nominee_review','pages':2,
        'title':'澳弘电子董事会薪酬与考核委员会关于2026年限制性股票激励计划首次授予激励对象名单的核查意见及公示情况说明'},
    '1225556866':{'code':'605058.SH','sha256':'c3406fc5ba9c78f1a7597dc913f3ae9978cfcb4ab812c22f0ac3198b24bd3ee9','type':'shareholder_meeting_material','pages':9,
        'title':'澳弘电子2026年第一次临时股东会会议资料'},
}
FIELDS=('ts_code','trade_date','public_time','title','event_id','event_type','independent_catalyst',
        'catalyst_quality','risk_penalty','severe_negative_event','concept_denial','source','source_sha256',
        'publication_time_source','publication_time_basis','publication_record_sha256',
        'official_announcement_id','display_announcement_id','new_on_target_trade_date')
BOOLS={'independent_catalyst','severe_negative_event','concept_denial','new_on_target_trade_date'}

def _read(path):
    def unique(pairs):
        output={}
        for k,v in pairs:
            if k in output:raise ValueError('announcement_duplicate_json_key:'+k)
            output[k]=v
        return output
    def reject(v):raise ValueError('announcement_nonfinite_json:'+v)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique,parse_constant=reject)

def _hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _binding(value, identities):
    if not isinstance(value,dict) or set(value)!={'path','sha256'}:raise ValueError('announcement_binding_structure')
    path=Path(value['path'])
    if not path.is_absolute() or not path.is_file() or not re.fullmatch('[0-9a-f]{64}',str(value['sha256'])):
        raise ValueError('announcement_binding_path_or_digest')
    actual=_hash(path)
    if actual!=value['sha256']:raise ValueError('announcement_binding_hash:'+path.name)
    identities[str(path.resolve())]=actual
    return path

def _stamp(value):
    text=str(value)
    # Eastmoney emits HH:MM:SS:millis, not an offset in the last component.
    if re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d:\d{3}',text):
        text=text[:-4]+'.'+text[-3:]+'+08:00'
    stamp=datetime.fromisoformat(text)
    if stamp.tzinfo is None:raise ValueError('announcement_timestamp_timezone_required')
    return stamp.astimezone(TZ)

def _date(value):
    if isinstance(value,(date,datetime)):return value.date() if isinstance(value,datetime) else value
    text=str(value)
    return datetime.strptime(text,'%Y%m%d').date() if re.fullmatch(r'\d{8}',text) else date.fromisoformat(text[:10])

def _bool(value):
    if type(value) is bool:return value
    if isinstance(value,str) and value.lower() in {'true','false','1','0'}:return value.lower() in {'true','1'}
    if type(value) is int and value in (0,1):return bool(value)
    raise ValueError('announcement_boolean_invalid')

def _null(value):
    return value is None or value=='' or isinstance(value,float) and math.isnan(value)

def _event(row, allow_extra=False):
    if not isinstance(row,dict) or not set(FIELDS)<=set(row):raise ValueError('announcement_event_fields_missing')
    if not allow_extra and set(row)-set(FIELDS):raise ValueError('announcement_unverified_event_columns')
    result={k:row[k] for k in FIELDS}
    for k in ('event_id','official_announcement_id'):
        if isinstance(row[k],bool) or not re.fullmatch(r'\d+',str(row[k])):raise ValueError('announcement_event_id_invalid')
        result[k]=str(row[k])
    result['trade_date']=_date(row['trade_date']).isoformat()
    result['public_time']=_stamp(row['public_time']).isoformat()
    for k in BOOLS:result[k]=_bool(row[k])
    for k in ('catalyst_quality','risk_penalty'):
        v=row[k]
        result[k]=(0.0 if k=='risk_penalty' else None) if _null(v) else float(v)
        if result[k] is not None and not math.isfinite(result[k]):raise ValueError('announcement_event_nonfinite')
    return result

def _pages(candidate,provider,request,mapping,identities):
    bindings=candidate.get('source_query_bindings',{}).get(provider)
    if not isinstance(bindings,list) or not bindings:raise ValueError('announcement_query_bindings_missing:'+provider)
    code=candidate['ts_code'];bare=code[:6]
    day=request['trade_date'];end=(_date(day)+timedelta(days=1)).isoformat()
    all_rows=[];sources=[];total=None
    for page,binding in enumerate(bindings,1):
        query=_read(_binding(binding,identities))
        expected_keys={'schema','source','code','url','method','request_parameters','started_at','retrieved_at','http_status','response','capture_kind'}
        if set(query)!=expected_keys:raise ValueError('announcement_query_envelope_fields')
        if query['schema']!='SHORT_BURST_ANNOUNCEMENT_QUERY_V1' or query['source']!=provider or query['code']!=code:
            raise ValueError('announcement_query_code_or_source')
        if type(query['http_status']) is not int or query['http_status']!=200:raise ValueError('announcement_http_status')
        if query['capture_kind']!='fresh_retrieval_of_fixed_historical_query':raise ValueError('announcement_capture_kind')
        begun=_stamp(query['started_at']);ended=_stamp(query['retrieved_at'])
        if ended<begun or begun<_stamp(day+'T15:00:00+08:00'):raise ValueError('announcement_capture_interval')
        if provider=='cninfo':
            expected={'stock':bare+','+mapping[bare],'tabName':'fulltext','pageSize':'100','pageNum':str(page),'column':'','category':'','plate':'','seDate':day+'~'+end,'searchkey':'','secid':'','sortName':'','sortType':'','isHLtitle':'false'}
            endpoint=CNINFO;method='POST'
        else:
            expected={'sr':-1,'page_size':100,'page_index':page,'ann_type':'A','client_source':'web','stock_list':bare,'f_node':0,'s_node':0,'begin_time':day,'end_time':end}
            endpoint=EASTMONEY;method='GET'
        if query['url']!=endpoint or query['method']!=method or query['request_parameters']!=expected:
            raise ValueError('announcement_request_identity:'+provider+':'+code)
        response_path=_binding(query['response'],identities);payload=_read(response_path);sources.append(query['response'])
        if provider=='cninfo':
            rows=payload.get('announcements')
            if rows is None:rows=[]
            count=payload.get('totalAnnouncement')
            if type(payload.get('hasMore')) is not bool:raise ValueError('announcement_cninfo_has_more_missing')
            if type(count) is not int or count<0 or payload.get('totalRecordNum')!=count:
                raise ValueError('announcement_cninfo_total_invalid')
            if payload['hasMore']!=(page*100<count):raise ValueError('announcement_cninfo_pagination_state')
            if payload.get('totalpages') not in ({0,1} if count<=100 else {(count+99)//100}):
                raise ValueError('announcement_cninfo_page_count')
        else:
            if type(payload.get('success')) is not int or payload['success']!=1 or payload.get('error')!='':
                raise ValueError('announcement_eastmoney_response_failed')
            data=payload.get('data',{});rows=data.get('list');count=data.get('total_hits')
            if data.get('page_index')!=page or data.get('page_size')!=100:raise ValueError('announcement_eastmoney_page_identity')
        if type(count) is not int or count<0 or not isinstance(rows,list):raise ValueError('announcement_rows_or_count')
        if total is None:total=count
        if total!=count:raise ValueError('announcement_count_changed_between_pages')
        if len(rows)!=max(0,min(100,count-(page-1)*100)):raise ValueError('announcement_incomplete_page')
        for row in rows:
            if not isinstance(row,dict):raise ValueError('announcement_row_not_object')
            if provider=='cninfo':
                if row.get('secCode')!=bare or row.get('orgId')!=mapping[bare]:raise ValueError('announcement_cninfo_wrong_security')
                stamp=datetime.fromtimestamp(float(row['announcementTime'])/1000,TZ)
                if not _date(day)<=stamp.date()<=_date(end):raise ValueError('announcement_cninfo_notice_date')
            else:
                if not any(x.get('stock_code')==bare for x in row.get('codes',[])):raise ValueError('announcement_eastmoney_wrong_security')
                if not _date(day)<=_date(row['notice_date'])<=_date(end):raise ValueError('announcement_eastmoney_notice_date')
            all_rows.append((row,query['response']['sha256']))
    if len(bindings)!=max(1,(total+99)//100) or len(all_rows)!=total:raise ValueError('announcement_missing_or_extra_page')
    idfield='announcementId' if provider=='cninfo' else 'art_code'
    ids=[row[idfield] for row,_ in all_rows]
    if len(set(ids))!=len(ids) or any(not isinstance(i,str) or not i for i in ids):raise ValueError('announcement_duplicate_or_missing_id')
    return all_rows,sources

def check(request, events, review):
    """Return independently recomputed evidence; raise ValueError on any mismatch.

    events accepts a DataFrame, list of dicts, or CSV path. Values normalized by
    the original store (risk null to zero, UTC timestamps) compare equivalently.
    """
    identities={}
    if not isinstance(request,dict) or not isinstance(review,dict):raise ValueError('announcement_request_or_review_invalid')
    cutoff=_stamp(request['as_of']);day=_date(request['trade_date'])
    if cutoff.date()!=day or cutoff.hour<15:raise ValueError('announcement_postclose_cutoff')
    if review.get('schema')!='NINE_COMPANY_ANNOUNCEMENT_REVIEW_V1' or review.get('trade_date')!=str(day) or _stamp(review['as_of'])!=cutoff:
        raise ValueError('announcement_review_identity')
    wanted=[s['code'] for s in request['stocks']]
    candidates=review.get('candidates')
    if not wanted or len(wanted)!=len(set(wanted)) or not isinstance(candidates,list) or len(candidates)!=len(wanted) or {c['ts_code'] for c in candidates}!=set(wanted):
        raise ValueError('announcement_candidate_scope')
    mapping_raw=_read(_binding(review.get('query_mapping_binding'),identities))
    mapping={}
    for row in mapping_raw['stockList']:
        if row.get('code') in {c[:6] for c in wanted}:
            if row['code'] in mapping:raise ValueError('announcement_duplicate_mapping')
            mapping[row['code']]=row['orgId']
    if set(mapping)!={c[:6] for c in wanted}:raise ValueError('announcement_mapping_scope')
    expected=[];excluded=[];documents={};source_pages=0
    for candidate in candidates:
        cn,cnpaths=_pages(candidate,'cninfo',request,mapping,identities)
        em,empaths=_pages(candidate,'eastmoney',request,mapping,identities)
        source_pages+=len(cnpaths)+len(empaths)
        declared=candidate.get('source_files',[])
        if sorted((x['path'],x['sha256']) for x in declared)!=sorted((x['path'],x['sha256']) for x in cnpaths+empaths):
            raise ValueError('announcement_source_file_scope')
        if candidate.get('cninfo_total')!=len(cn) or candidate.get('eastmoney_total')!=len(em):raise ValueError('announcement_reported_total_mismatch')
        if candidate.get('all_public_events_complete') is not False:raise ValueError('announcement_source_scope_overclaim')
        matched=set();current_count=0
        for official,_ in cn:
            matching=[(item,checksum) for item,checksum in em if item['title'].split(':',1)[-1]==official['announcementTitle']]
            if len(matching)!=1:raise ValueError('announcement_cross_source_title_identity')
            display,checksum=matching[0]
            if display['art_code'] in matched:raise ValueError('announcement_cross_source_duplicate_match')
            matched.add(display['art_code']);published=_stamp(display['display_time'])
            event_id=official['announcementId'];code=candidate['ts_code']
            if published>cutoff:
                excluded.append({'code':code,'event_id':event_id,'public_time':published.isoformat(),'reason':'after_as_of'});continue
            policy=APPROVED_DOCUMENTS.get(event_id)
            if policy is None:raise ValueError('announcement_document_review_not_registered:'+event_id)
            if code!=policy['code'] or official['announcementTitle']!=policy['title']:raise ValueError('announcement_document_review_identity')
            binding=review.get('document_bindings',{}).get(event_id)
            path=_binding(binding,identities)
            if binding['sha256']!=policy['sha256'] or not path.read_bytes().startswith(b'%PDF-'):
                raise ValueError('announcement_reviewed_pdf_content_changed')
            documents[event_id]=binding
            adjunct=official.get('adjunctUrl','')
            if not re.fullmatch(r'finalpage/\d{4}-\d\d-\d\d/'+re.escape(event_id)+r'\.PDF',adjunct):raise ValueError('announcement_pdf_url_identity')
            current_count+=published.date()==day
            expected.append({'ts_code':code,'trade_date':published.date().isoformat(),'public_time':published.isoformat(),
                'title':official['announcementTitle'],'event_id':event_id,'event_type':policy['type'],
                'independent_catalyst':False,'catalyst_quality':None,'risk_penalty':0.0,'severe_negative_event':False,'concept_denial':False,
                'source':'https://static.cninfo.com.cn/'+adjunct,'source_sha256':policy['sha256'],
                'publication_time_source':EASTMONEY,'publication_time_basis':PUBLICATION_BASIS,'publication_record_sha256':checksum,
                'official_announcement_id':event_id,'display_announcement_id':display['art_code'],'new_on_target_trade_date':published.date()==day})
        if len(matched)!=len(em):raise ValueError('announcement_unmatched_eastmoney_record')
        if candidate.get('target_day_new_announcements')!=current_count:raise ValueError('announcement_target_day_count')
    if set(review.get('document_bindings',{}))!=set(documents):raise ValueError('announcement_document_binding_scope')
    def ordered(rows):
        ids=[(r['ts_code'],r['event_id']) for r in rows]
        if len(set(ids))!=len(ids):raise ValueError('announcement_duplicate_event')
        return sorted(rows,key=lambda r:(r['ts_code'],r['event_id']))
    expected=ordered(expected)
    if ordered([_event(r,allow_extra=True) for r in review.get('events',[])])!=expected:raise ValueError('announcement_review_events_replay_mismatch')
    if isinstance(events,(str,Path)):
        with Path(events).open(encoding='utf-8-sig',newline='') as stream:events=list(csv.DictReader(stream))
    elif hasattr(events,'to_dict'):events=events.to_dict('records')
    if not isinstance(events,list):raise ValueError('announcement_consumed_events_structure')
    actual=ordered([_event(r) for r in events])
    if any(_stamp(r['public_time'])>cutoff for r in actual):raise ValueError('announcement_future_event_consumed')
    if actual!=expected:raise ValueError('announcement_consumed_events_replay_mismatch')
    if review.get('event_count')!=len(expected) or review.get('stock_count')!=len(wanted) or review.get('t_day_new_event_count')!=sum(r['new_on_target_trade_date'] for r in expected):
        raise ValueError('announcement_review_counts_mismatch')
    if review.get('all_public_events_complete') is not False:raise ValueError('announcement_all_public_scope_overclaim')
    for path,checksum in identities.items():
        if _hash(path)!=checksum:raise ValueError('announcement_source_changed_during_replay')
    return {'schema':'SHORT_BURST_ANNOUNCEMENT_SOURCE_REPLAY_V1','status':'PASS','data_date':str(day),'as_of':cutoff.isoformat(),
        'candidate_count':len(wanted),'source_page_count':source_pages,'reviewed_document_count':len(documents),'event_count':len(expected),
        't_day_new_event_count':sum(r['new_on_target_trade_date'] for r in expected),'excluded_after_as_of':excluded,
        'scope':'bound_cninfo_and_eastmoney_company_announcements_for_requested_securities',
        'all_public_events_complete':False,'numeric_catalyst_or_risk_inferred':False,
        'verified_steps':['every_query_code_date_endpoint_and_page_rechecked','source_success_totals_and_complete_pagination_recomputed',
            'cross_source_announcements_and_publication_times_rebuilt','reviewed_pdf_bytes_and_neutral_document_policy_bound',
            'all_consumed_event_fields_and_counts_compared'],
        'source_bindings':identities,'document_bindings':documents}

def check_event_sources(request, review, events=None):
    """Convenience entry; use the same normalized event reader as the pipeline."""
    if events is None:
        import pandas as pd
        from .data import NormalizedStore
        frame=NormalizedStore(request['data_root'],strict=True).event_features()
        if frame is None:raise ValueError('announcement_consumed_events_missing')
        published=pd.to_datetime(frame['public_time'],utc=True,errors='raise')
        dates=pd.to_datetime(frame['trade_date'],errors='raise').dt.normalize()
        events=frame[(published<=pd.Timestamp(request['as_of'])) &
                     (dates<=pd.Timestamp(request['trade_date']))].copy()
    return check(request,events,review)
