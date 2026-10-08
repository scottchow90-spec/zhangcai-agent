"""Portable source replay adversarial tests with temporary synthetic fixtures."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:
    from lhbpost import event_source_replay as replay
except ImportError:
    import event_source_replay as replay

class EventSourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='event-replay-tests-')
        self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.code='600207.SH';self.event_id='1225560326';self.title='安彩高科关于筹划资产出售暨关联交易的提示性公告'
        self.request={'trade_date':'2026-09-11','as_of':'2026-09-11T23:59:59+08:00','stocks':[{'code':self.code}]}
        pdf=self.root/'source.pdf';pdf.write_bytes(b'%PDF-1.4\nsynthetic test document\n%%EOF')
        self.pdf={'path':str(pdf),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
        policy=dict(replay.APPROVED_DOCUMENTS[self.event_id],sha256=self.pdf['sha256'])
        p=patch.dict(replay.APPROVED_DOCUMENTS,{self.event_id:policy});p.start();self.addCleanup(p.stop)
        mapping=self.save('mapping.json',{'stockList':[{'code':'600207','orgId':'gssh0600207'}]})
        self.cn={'totalAnnouncement':1,'totalRecordNum':1,'totalpages':0,'hasMore':False,'announcements':[
          {'announcementId':self.event_id,'secCode':'600207','orgId':'gssh0600207','announcementTitle':self.title,
           'announcementTime':1789142400000,'adjunctUrl':'finalpage/2026-09-12/'+self.event_id+'.PDF'}]}
        self.em={'success':1,'error':'','data':{'page_index':1,'page_size':100,'total_hits':1,'list':[
          {'art_code':'AN202609111829273998','codes':[{'stock_code':'600207'}],'title':'安彩高科:'+self.title,
           'notice_date':'2026-09-12 00:00:00','display_time':'2026-09-11 17:37:23:389'}]}}
        self.query={}
        for source,payload in [('cninfo',self.cn),('eastmoney',self.em)]:
            params={'stock':'600207,gssh0600207','tabName':'fulltext','pageSize':'100','pageNum':'1','column':'','category':'','plate':'','seDate':'2026-09-11~2026-09-12','searchkey':'','secid':'','sortName':'','sortType':'','isHLtitle':'false'} if source=='cninfo' else {'sr':-1,'page_size':100,'page_index':1,'ann_type':'A','client_source':'web','stock_list':'600207','f_node':0,'s_node':0,'begin_time':'2026-09-11','end_time':'2026-09-12'}
            self.query[source]={'schema':'SHORT_BURST_ANNOUNCEMENT_QUERY_V1','source':source,'code':self.code,
              'url':replay.CNINFO if source=='cninfo' else replay.EASTMONEY,'method':'POST' if source=='cninfo' else 'GET',
              'request_parameters':params,'started_at':'2026-09-12T01:00:00+08:00','retrieved_at':'2026-09-12T01:00:01+08:00','http_status':200,
              'response':self.save(source+'.response.json',payload),'capture_kind':'fresh_retrieval_of_fixed_historical_query'}
        candidate={'ts_code':self.code,'cninfo_total':1,'eastmoney_total':1,'all_public_events_complete':False,'target_day_new_announcements':1,
                   'source_query_bindings':{p:[self.save(p+'.query.json',q)] for p,q in self.query.items()},
                   'source_files':[q['response'] for q in self.query.values()]}
        self.event={'ts_code':self.code,'trade_date':'20260911','public_time':'2026-09-11T17:37:23.389000+08:00','title':self.title,
             'event_id':self.event_id,'event_type':'asset_sale_related_party_intention','independent_catalyst':False,'catalyst_quality':None,
             'risk_penalty':None,'severe_negative_event':False,'concept_denial':False,
             'source':'https://static.cninfo.com.cn/finalpage/2026-09-12/'+self.event_id+'.PDF','source_sha256':self.pdf['sha256'],
             'publication_time_source':replay.EASTMONEY,'publication_time_basis':replay.PUBLICATION_BASIS,
             'publication_record_sha256':self.query['eastmoney']['response']['sha256'],
             'official_announcement_id':self.event_id,'display_announcement_id':'AN202609111829273998','new_on_target_trade_date':True}
        self.events=[copy.deepcopy(self.event)]
        self.review={'schema':'NINE_COMPANY_ANNOUNCEMENT_REVIEW_V1','trade_date':self.request['trade_date'],'as_of':self.request['as_of'],
              'stock_count':1,'event_count':1,'t_day_new_event_count':1,'candidates':[candidate],'query_mapping_binding':mapping,
              'document_bindings':{self.event_id:self.pdf},'events':[copy.deepcopy(self.event)],'all_public_events_complete':False}

    def save(self,name,obj):
        path=self.root/name;path.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

    def refresh(self,source,payload=None):
        if payload is not None:self.query[source]['response']=self.save(source+'.response.json',payload)
        candidate=self.review['candidates'][0]
        candidate['source_query_bindings'][source]=[self.save(source+'.query.json',self.query[source])]
        candidate['source_files']=[q['response'] for q in self.query.values()]
        if source=='eastmoney':
            for event in [*self.events,*self.review['events']]:event['publication_record_sha256']=self.query[source]['response']['sha256']

    def check(self):return replay.check(self.request,self.events,self.review)

    def test_real_structure_replayed(self):
        result=self.check();self.assertEqual(result['status'],'PASS');self.assertEqual(result['event_count'],1)
        self.assertFalse(result['all_public_events_complete'])

    def test_success_booleans_not_used_as_proof(self):
        self.review['source_query_coverage_complete']=False
        self.review['candidates'][0]['cninfo_query_success']=False
        self.assertEqual(self.check()['status'],'PASS')

    def test_missing_query_envelope_rejected(self):
        del self.review['candidates'][0]['source_query_bindings']['cninfo']
        with self.assertRaisesRegex(ValueError,'query_bindings_missing'):self.check()

    def test_wrong_empty_stock_request_rejected(self):
        self.query['cninfo']['request_parameters']['stock']='600088,gssh0600088';self.refresh('cninfo')
        with self.assertRaisesRegex(ValueError,'request_identity'):self.check()

    def test_wrong_response_stock_rejected_even_rehashed(self):
        self.cn['announcements'][0]['secCode']='600088';self.refresh('cninfo',self.cn)
        with self.assertRaisesRegex(ValueError,'wrong_security'):self.check()

    def test_wrong_query_date_rejected(self):
        self.query['eastmoney']['request_parameters']['begin_time']='2026-09-12';self.refresh('eastmoney')
        with self.assertRaisesRegex(ValueError,'request_identity'):self.check()

    def test_missing_page_rejected(self):
        self.review['candidates'][0]['source_query_bindings']['eastmoney']=[]
        with self.assertRaisesRegex(ValueError,'query_bindings_missing'):self.check()

    def test_payload_count_cannot_hide_missing_items(self):
        self.em['data']['total_hits']=2;self.refresh('eastmoney',self.em)
        with self.assertRaisesRegex(ValueError,'incomplete_page'):self.check()

    def test_extra_page_rejected(self):
        pages=self.review['candidates'][0]['source_query_bindings']['cninfo'];pages.append(copy.deepcopy(pages[0]))
        with self.assertRaisesRegex(ValueError,'request_identity'):self.check()

    def test_missing_announcement_rejected(self):
        self.events=[]
        with self.assertRaisesRegex(ValueError,'consumed_events_replay_mismatch'):self.check()

    def test_missing_review_announcement_rejected(self):
        self.review['events']=[]
        with self.assertRaisesRegex(ValueError,'review_events_replay_mismatch'):self.check()

    def test_future_consumed_event_rejected(self):
        self.events[0]['public_time']='2026-09-12T00:00:01+08:00'
        with self.assertRaisesRegex(ValueError,'future_event_consumed'):self.check()

    def test_invented_catalyst_and_risk_rejected(self):
        for field,value in [('independent_catalyst',True),('catalyst_quality',0.8),('risk_penalty',0.5),('severe_negative_event',True)]:
            with self.subTest(field=field):
                old=self.events[0][field];self.events[0][field]=value
                with self.assertRaisesRegex(ValueError,'consumed_events_replay_mismatch'):self.check()
                self.events[0][field]=old

    def test_unregistered_document_rejected(self):
        self.cn['announcements'][0]['announcementId']='9999999999';self.refresh('cninfo',self.cn)
        with self.assertRaisesRegex(ValueError,'document_review_not_registered'):self.check()

    def test_changed_reviewed_document_rejected(self):
        path=Path(self.pdf['path']);path.write_bytes(b'%PDF-1.4\nchanged content')
        self.pdf['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'reviewed_pdf_content_changed'):self.check()

    def test_false_all_public_claim_rejected(self):
        self.review['all_public_events_complete']=True
        with self.assertRaisesRegex(ValueError,'all_public_scope_overclaim'):self.check()

    def test_unverified_extra_event_field_rejected(self):
        self.events[0]['next_close_return']=0.1
        with self.assertRaisesRegex(ValueError,'unverified_event_columns'):self.check()

    def test_after_cutoff_source_is_excluded_not_backfilled(self):
        self.em['data']['list'][0]['display_time']='2026-09-12 00:00:01:000';self.refresh('eastmoney',self.em)
        self.events=[];self.review['events']=[];self.review['document_bindings']={}
        self.review['event_count']=0;self.review['t_day_new_event_count']=0;self.review['candidates'][0]['target_day_new_announcements']=0
        result=self.check();self.assertEqual(result['event_count'],0);self.assertEqual(len(result['excluded_after_as_of']),1)

if __name__=='__main__':unittest.main()
