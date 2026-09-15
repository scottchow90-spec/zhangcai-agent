import hashlib
import pytest
from lhbpost.data import non_equity_scope as scope
from lhbpost.data.local_postmarket import _code

@pytest.fixture
def bound(tmp_path,monkeypatch):
    code='821001';record=bytearray(360);record[:6]=code.encode();name='24京资01'
    encoded=name.encode('gbk');record[31:31+len(encoded)]=encoded;record[76:80]=(4).to_bytes(4,'little')
    master=tmp_path/'bjs.tnf';master.write_bytes(bytes(50)+record)
    day=tmp_path/'bj821001.day';day.write_bytes(bytes(32))
    monkeypatch.setattr(scope,'TNF_SOURCE',str(master))
    monkeypatch.setattr(scope,'VERIFIED_NON_EQUITY',{code:{'name':name,'classification':'corporate_bond',
        'tnf_record_offset':50,'tnf_record_sha256':hashlib.sha256(record).hexdigest(),'tnf_security_type_raw':4}})
    return master,day

def test_only_attested_bond_excluded(bound):
    assert scope.verified_bond_identity('821001')
    with pytest.raises(ValueError,match='verified_non_equity_bond'):_code('821001')
    result=scope.exclusion_record('821001',bound[1])
    assert result['original_file_preserved'] and result['raw_sha256']==hashlib.sha256(bytes(32)).hexdigest()
    assert bound[1].read_bytes()==bytes(32)

@pytest.mark.parametrize('change',['class','name','layout','missing'])
def test_changed_or_missing_identity_retained_for_review(bound,change):
    master,day=bound
    if change in ('class','name'):
        b=bytearray(master.read_bytes());b[50+(76 if change=='class' else 31)]=2;master.write_bytes(b)
    elif change=='layout':master.write_bytes(master.read_bytes()+b'x')
    else:master.unlink()
    assert not scope.verified_bond_identity('821001')
    assert _code('821001')=='821001.BJ'
    with pytest.raises(ValueError,match='not_verified'):scope.exclusion_record('821001',day)

def test_cdr_and_unverified_prefix_are_not_excluded(bound):
    assert _code('689009')=='689009.SH'
    assert _code('821099')=='821099.BJ'
    assert _code('920001')=='920001.BJ'

def test_normal_quote_updates_keep_bond_class_and_record_new_hash(bound):
    master,day=bound
    day.write_bytes(bytes(64))
    b=bytearray(master.read_bytes());b[50+100]=42;master.write_bytes(b)
    assert scope.verified_bond_identity('821001')
    with pytest.raises(ValueError,match='verified_non_equity_bond'):_code('821001')
    evidence=scope.exclusion_record('821001',day)
    assert evidence['raw_bytes']==64 and evidence['raw_sha256']==hashlib.sha256(bytes(64)).hexdigest()
    assert evidence['tnf_record_sha256']==hashlib.sha256(b[50:]).hexdigest()

def test_record_reordering_does_not_change_security_identity(bound):
    master,day=bound
    b=master.read_bytes();master.write_bytes(b[:50]+bytes(360)+b[50:])
    assert scope.verified_bond_identity('821001')
    assert scope.exclusion_record('821001',day)['tnf_record_offset']==410
