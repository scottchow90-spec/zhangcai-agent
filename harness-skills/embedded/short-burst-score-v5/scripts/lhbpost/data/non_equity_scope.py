"""Exact known non-equity identities, verified against local security master.

Not a failure-driven denylist: each exact code has same-code bond name/type proof.
Unverified prefixes and equity CDR 689009 are not silently excluded.
"""
from pathlib import Path
import hashlib
import sys
_app_scripts_dir = str(Path(__file__).resolve().parents[6] / 'scripts')
if _app_scripts_dir not in sys.path: sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_tdx_root

TNF_SOURCE = str(resolve_tdx_root() / 'T0002' / 'hq_cache' / 'bjs.tnf')
TNF_SOURCE_SHA256 = '01bcfee6b3283178db6b567009e8df8e80f9c03982470191ff1dc11221345b17'
VERIFIED_NON_EQUITY = {'810011': {'name': '优机定转', 'classification': 'directed_convertible_bond', 'tnf_record_offset': 770, 'tnf_record_sha256': 'c5dec670fd9569b85a0eec4540fc4a178f489cbd4a298d005168d7d2221343a8', 'tnf_security_type_raw': 4}, '810014': {'name': '莱特定转', 'classification': 'directed_convertible_bond', 'tnf_record_offset': 1490, 'tnf_record_sha256': '0fbb3f975021f123a455c58addc31d7b036fe0626f5f0db5107d235107692f70', 'tnf_security_type_raw': 4}, '821001': {'name': '24京资01', 'classification': 'corporate_bond', 'tnf_record_offset': 1850, 'tnf_record_sha256': 'bee882c22637cf4850cc6cb69cee110fc5982e2a9e411a6b4323162705088900', 'tnf_security_type_raw': 4}, '821003': {'name': '24智都01', 'classification': 'corporate_bond', 'tnf_record_offset': 2570, 'tnf_record_sha256': '41dad55b04eaf288fb2933c08df5b1322ab894937529347cb11f6195b30d099d', 'tnf_security_type_raw': 4}, '821010': {'name': 'MY赣融01', 'classification': 'corporate_bond', 'tnf_record_offset': 4010, 'tnf_record_sha256': '599aaefcb7db9e9d3d863b9c8ffa11045cd1c128eae31a84a5984840caf2dc7b', 'tnf_security_type_raw': 4}, '821014': {'name': '25川商01', 'classification': 'corporate_bond', 'tnf_record_offset': 5090, 'tnf_record_sha256': '308ea19b4309ea02dbf5fb0b8d93dbf95133b35648bf0eefea5144e31b231892', 'tnf_security_type_raw': 4}, '821015': {'name': 'K25中资1', 'classification': 'corporate_bond', 'tnf_record_offset': 5450, 'tnf_record_sha256': '2e3c247a7fc05319d6db24dd5b0163d9b86fd5bf631735dd06cd83a5326c33c0', 'tnf_security_type_raw': 4}, '821022': {'name': 'S26雄集1', 'classification': 'corporate_bond', 'tnf_record_offset': 7250, 'tnf_record_sha256': '79d1ec30261b9a19416a1c24d344328a223ae4bd8681319166d5d76302133934', 'tnf_security_type_raw': 4}, '821023': {'name': 'K26湖产3', 'classification': 'corporate_bond', 'tnf_record_offset': 7610, 'tnf_record_sha256': '144ff5300c49233e8c7b809453fb8539de98b530dca170f3cd5a0c57eb52e3d1', 'tnf_security_type_raw': 4}, '821024': {'name': 'K26苏金1', 'classification': 'corporate_bond', 'tnf_record_offset': 7970, 'tnf_record_sha256': '86b3ed98216ccfda4ab1c2f9527f59f9c643525df64ac23953deb66a03e21cf4', 'tnf_security_type_raw': 4}}

def _current_identity(code, tnf_path=None):
    if code not in VERIFIED_NON_EQUITY: raise ValueError('security_not_attested')
    source=Path(tnf_path or TNF_SOURCE);before=source.stat();master=source.read_bytes();after=source.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('security_master_changed_during_read')
    if len(master)<50 or (len(master)-50)%360:
        raise ValueError('security_master_record_layout_invalid')
    records=[(off,master[off:off+360]) for off in range(50,len(master),360)
             if master[off:off+6]==code.encode('ascii')]
    if len(records)!=1: raise ValueError('security_master_identity_missing_or_duplicate')
    off,record=records[0];expected=VERIFIED_NON_EQUITY[code]
    if record[6]!=0: raise ValueError('security_master_code_layout_invalid')
    end=record.find(b'\0',31,76)
    if end<0: raise ValueError('security_master_name_layout_invalid')
    if record[31:end].decode('gbk')!=expected['name']:
        raise ValueError('security_master_name_changed')
    if int.from_bytes(record[76:80],'little')!=4:
        raise ValueError('security_master_class_changed')
    return {'security_master_source':str(source.resolve()),
            'security_master_sha256':hashlib.sha256(master).hexdigest(),
            'tnf_record_offset':off,'tnf_record_sha256':hashlib.sha256(record).hexdigest(),
            'tnf_security_type_raw':4}

def verified_bond_identity(code, tnf_path=None, day_path=None):
    """Verify stable identity fields; ordinary quote updates do not change class.

    day_path remains a compatible unused argument: quote bytes are recorded in
    exclusion evidence, not interpreted as the security's instrument class.
    """
    try:
        _current_identity(code,tnf_path)
        return True
    except (OSError,ValueError,UnicodeError): return False

def exclusion_record(code, path):
    try: current=_current_identity(code)
    except (OSError,ValueError,UnicodeError) as exc:
        raise ValueError('security_classification_not_verified') from exc
    p=Path(path);before=p.stat();raw=p.read_bytes();after=p.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('excluded_source_changed_during_read')
    return {'ts_code':code+'.BJ','reason':'verified_non_equity_bond',
            'name':VERIFIED_NON_EQUITY[code]['name'],
            'classification':VERIFIED_NON_EQUITY[code]['classification'],
            **current,'raw_path':str(p.resolve()),
            'initial_classification_evidence_sha256':TNF_SOURCE_SHA256,
            'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'original_file_preserved':True}
