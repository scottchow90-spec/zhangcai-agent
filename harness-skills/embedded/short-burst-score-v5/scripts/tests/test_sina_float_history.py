import tempfile, unittest
from pathlib import Path
try:
    from lhbpost.data.sina_float_history import parse_float_history, float_as_of, derive_observed_metrics, acquire_float_history
except ImportError:
    from sina_float_history import parse_float_history, float_as_of, derive_observed_metrics, acquire_float_history

def body(rows): return ('var KKE_ShareAmount_sz000638=('+rows+');').encode()

class FloatHistoryTests(unittest.TestCase):
    def test_units_temporal_and_unknown_totals(self):
        rows=parse_float_history(body('[{date:"2026-01-02",amount:"125.25"},{date:"2026-03-01",amount:200}]'),'sz000638')
        self.assertIsNone(float_as_of(rows,'sz000638','2026-01-01'))
        first=float_as_of(rows,'sz000638','2026-02-28')
        self.assertEqual(first['float_share'],1252500)
        self.assertIsNone(first['total_share']); self.assertIsNone(first['free_share'])
        self.assertFalse(first['publication_time_archive_verified'])
        self.assertEqual(float_as_of(rows,'sz000638','2026-03-01')['float_share'],2000000)
    def test_metrics_do_not_infer_total_cap(self):
        rows=parse_float_history(body('[["2026-01-01",100]]'),'sz000638')
        value=derive_observed_metrics(rows,'sz000638','2026-02-01',unadjusted_close=10,volume_shares=50000)
        self.assertEqual(value['circ_mv_yuan'],10000000)
        self.assertEqual(value['turnover_rate_percent'],5)
        self.assertIsNone(value['total_mv_yuan'])
    def test_wrong_symbol_and_executable_tail(self):
        for raw in [body('[["2026-01-01",100]]').replace(b'sz000638',b'sz002231'),body('[["2026-01-01",100]]')+b'alert(1)']:
            with self.assertRaises(ValueError):parse_float_history(raw,'sz000638')
    def test_invalid_and_ambiguous_rows(self):
        for rows in ['[]','[["2026-02-30",1]]','[["2026-01-01",0]]','[["2026-01-01",-1]]','[["2026-01-01","NaN"]]','[["2026-01-01",0.00001]]','[["2026-01-01",1],["2026-01-01",2]]','[{date:"2026-01-01",total:100}]']:
            with self.subTest(rows=rows),self.assertRaises(ValueError):parse_float_history(body(rows),'sz000638')
    def test_raw_retained_when_schema_fails(self):
        raw=body('[{date:"2026-01-01",unknown:100}]')
        with tempfile.TemporaryDirectory() as root:
            result=acquire_float_history('sz000638',root,fetch=lambda u,t:raw)
            self.assertEqual(result['status'],'FAILED')
            self.assertEqual((Path(root)/result['raw_file']).read_bytes(),raw)
    def test_success_fixture_fetch(self):
        with tempfile.TemporaryDirectory() as root:
            result=acquire_float_history('sz000638',root,fetch=lambda u,t:body('[["2026-01-01",100]]'))
            self.assertEqual(result['status'],'OBSERVED_EFFECTIVE_HISTORY')
            self.assertIn('symbol=sz000638',result['url'])

if __name__=='__main__':unittest.main()
