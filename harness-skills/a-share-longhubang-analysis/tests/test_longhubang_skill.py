from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import gzip, hashlib, importlib.util, json, subprocess, sys, tempfile, unittest
from decimal import Decimal, ROUND_HALF_EVEN
from unittest import mock
from pathlib import Path
from PIL import Image

HOME = Path(r"D:\C盘转移\日志\codex")
SKILL = HOME / "skills" / "a-share-longhubang-analysis"
WORKFLOW = SKILL / "scripts" / "longhubang_workflow.py"
POSTER_BUILDER = SKILL / "scripts" / "poster_builder.py"
POSTER_VALIDATOR = SKILL / "scripts" / "poster_validator.py"
CANONICAL_ADAPTER = SKILL / "scripts" / "canonical_business_adapter.py"
YOUZI_PROFILES = HOME / "knowledge-base" / "personal-investment" / "historical-a-share-kb" / "data" / "youzi" / "youzi_profiles.json"
CONTRACTS = HOME / "skills" / "stock-unified" / "references" / "stock_execution_contracts.json"
ROUTER = HOME / "scripts" / "stock_canonical_runtime.py"

def load_local_script(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module); return module

def load_poster_builder():
    return load_local_script("a_share_longhubang_poster_builder", POSTER_BUILDER)

def load_poster_validator():
    poster_builder = load_poster_builder()
    with mock.patch.dict(sys.modules, {"poster_builder": poster_builder}):
        return load_local_script("a_share_longhubang_poster_validator", POSTER_VALIDATOR)

def load_workflow():
    poster_builder = load_poster_builder()
    with mock.patch.dict(sys.modules, {"poster_builder": poster_builder}):
        return load_local_script("a_share_longhubang_workflow", WORKFLOW)

def load_canonical_adapter():
    return load_local_script("a_share_longhubang_canonical_adapter", CANONICAL_ADAPTER)

class LonghubangSkillContractTest(unittest.TestCase):
    def test_canonical_adapter_builds_clean_current_data_gate(self):
        module = load_canonical_adapter()
        payload = {
            "schema": "A_SHARE_LONGHUBANG_ANALYSIS_V1",
            "status": "CLEAN_PASS",
            "trade_date": "2026-09-01",
            "stock_count": 1,
            "stocks": [{
                "code": "000001", "name": "样本", "net_amount": 60_000_000,
                "buy_amount": 80_000_000, "sell_amount": 20_000_000,
                "reason": "日涨幅偏离值达到7%的前5只证券", "concept": "金融科技",
                "concept_evidence": {"main_business": ["银行业务"], "precise_concepts": ["金融科技"]},
            }],
            "sources": {"eastmoney": {"status": "CLEAN_PASS"}, "duanxianxia": {"status": "CLEAN_PASS"}, "lianban": {"status": "CLEAN_PASS"}},
        }
        environment = {
            "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
            "CODEX_STOCK_EVIDENCE_SET_ID": "sha256:" + "a" * 64,
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": "2026-09-01",
            "CODEX_DUANXIANXIA_STATUS": "CLEAN_PASS",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "analysis.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            gate = module.build_data_gate(path, environment)
        self.assertEqual("CLEAN_PASS", gate["status"])
        self.assertEqual([], gate["errors"])
        self.assertEqual({"identity", "effective_trading_date", "quote_kline", "fundamentals", "news_announcements", "sector_theme", "source_freshness"}, set(gate["dimensions"]))
        self.assertTrue(all(item["status"] == "CLEAN_PASS" and item["evidence_ids"] for item in gate["dimensions"].values()))

    def test_canonical_adapter_blocks_missing_fundamental_evidence(self):
        module = load_canonical_adapter()
        payload = {
            "schema": "A_SHARE_LONGHUBANG_ANALYSIS_V1", "status": "CLEAN_PASS",
            "trade_date": "2026-09-01", "stock_count": 1,
            "stocks": [{"code": "000001", "name": "样本", "net_amount": 60_000_000, "buy_amount": 80_000_000, "sell_amount": 20_000_000, "reason": "上榜原因", "concept": "金融科技", "concept_evidence": {"main_business": [], "precise_concepts": ["金融科技"]}}],
            "sources": {"duanxianxia": {"status": "CLEAN_PASS"}, "lianban": {"status": "CLEAN_PASS"}},
        }
        environment = {"CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS", "CODEX_STOCK_EVIDENCE_SET_ID": "sha256:" + "a" * 64, "CODEX_STOCK_EVIDENCE_TRADING_DATE": "2026-09-01", "CODEX_DUANXIANXIA_STATUS": "CLEAN_PASS"}
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "analysis.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            gate = module.build_data_gate(path, environment)
        self.assertEqual("BLOCKED", gate["status"])
        self.assertEqual("BLOCKED", gate["dimensions"]["fundamentals"]["status"])
        self.assertIn("data_gate_dimension_failed:fundamentals", gate["errors"])

    def test_local_poster_modules_ignore_cross_skill_module_cache(self):
        foreign_builder = mock.MagicMock(__file__=r"F:\foreign-skill\poster_builder.py")
        foreign_validator = mock.MagicMock(__file__=r"F:\foreign-skill\poster_validator.py")
        with mock.patch.dict(
            sys.modules,
            {"poster_builder": foreign_builder, "poster_validator": foreign_validator},
        ):
            poster_builder = load_poster_builder()
            poster_validator = load_poster_validator()
        self.assertEqual(SKILL / "scripts" / "poster_builder.py", Path(poster_builder.__file__).resolve())
        self.assertEqual(SKILL / "scripts" / "poster_validator.py", Path(poster_validator.__file__).resolve())
        self.assertTrue(callable(poster_builder.validate_conclusions))
        self.assertTrue(callable(poster_validator.validate))

    def test_required_files_and_metadata(self):
        required = [SKILL / "SKILL.md", SKILL / "agents" / "openai.yaml", SKILL / "scripts" / "codex_entry.py", WORKFLOW, SKILL / "scripts" / "poster_builder.py", SKILL / "scripts" / "poster_validator.py", SKILL / "references" / "workflow.md"]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])
        self.assertIn('display_name: "龙虎榜分析"', (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    def test_youzi_profile_catalog_is_complete_and_contract_bound(self):
        payload = json.loads(YOUZI_PROFILES.read_text(encoding="utf-8-sig"))
        profiles = payload.get("游资档案") or []
        self.assertGreaterEqual(len(profiles), 100)
        self.assertGreaterEqual(sum(len(profile.get("seats") or profile.get("关联席位") or []) for profile in profiles), 275)
        self.assertTrue(all(profile.get("name") or profile.get("规范名称") or profile.get("标准化名称") for profile in profiles))

        contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))["contracts"]
        contract = next(row for row in contracts if row["skill_id"] == "a-share-longhubang-analysis")
        bindings = {Path(row["path"]).resolve(): row["sha256"] for row in contract["business_bindings"]}
        self.assertIn(YOUZI_PROFILES.resolve(), bindings)
        self.assertEqual(hashlib.sha256(YOUZI_PROFILES.read_bytes()).hexdigest(), bindings[YOUZI_PROFILES.resolve()])

    def test_exact_chinese_route(self):
        result = subprocess.run([sys.executable, str(ROUTER), "route", "--query", "龙虎榜分析"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(0, result.returncode, result.stderr); payload = json.loads(result.stdout)
        self.assertEqual(["a-share-longhubang-analysis"], payload["skill_ids"]); self.assertEqual("exact_workflow_name", payload["matches"][0]["match_type"])

    def test_fetch_json_decodes_gzip_response_body(self):
        module = load_workflow()
        expected = {"status": "ok", "rows": [{"code": "300598"}]}
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = gzip.compress(
            json.dumps(expected).encode("utf-8")
        )
        with mock.patch.object(module.urllib.request, "urlopen", return_value=response):
            self.assertEqual(expected, module.fetch_json("https://example.invalid/data", retries=1))

    def test_filter_and_poster_policy(self):
        module = load_workflow()
        rows = [
            {"SECURITY_CODE": "300001", "SECURITY_NAME_ABBR": "甲", "BILLBOARD_NET_AMT": 50_000_001, "EXPLANATION": "连续三个交易日内"},
            {"SECURITY_CODE": "300001", "SECURITY_NAME_ABBR": "甲", "BILLBOARD_NET_AMT": 60_000_000},
            {"SECURITY_CODE": "123001", "SECURITY_NAME_ABBR": "转债", "BILLBOARD_NET_AMT": 90_000_000},
            {"SECURITY_CODE": "600001", "SECURITY_NAME_ABBR": "乙", "BILLBOARD_NET_AMT": 50_000_000},
        ]
        self.assertEqual(["300001"], [item["code"] for item in module.select_equities(rows)])
        self.assertEqual(160, module.POSTER_POLICY["min_source_font_px"]); self.assertEqual(228, module.POSTER_POLICY["body_source_font_px"]); self.assertEqual(320, module.POSTER_POLICY["heading_source_font_px"]); self.assertEqual(242, module.POSTER_POLICY["primary_source_font_px"]); self.assertEqual(1080, module.POSTER_POLICY["preview_width"]); self.assertEqual(22, module.POSTER_POLICY["max_line_chars"]); self.assertTrue(module.POSTER_POLICY["light_background_gate_required"]); self.assertTrue(module.POSTER_POLICY["paginate_instead_of_truncate"])

    def test_derived_conclusions_are_quantified_and_cover_multiple_dimensions(self):
        module = load_workflow()
        records = [
            {"code": "300001", "name": "甲", "net_amount": 100_000_000, "concept": "芯片、算力", "representative_seat": "深股通专用", "top_trader": "北向资金", "reason": "日涨幅达到15%的前5只证券", "three_day": False},
            {"code": "688001", "name": "乙", "net_amount": 80_000_000, "concept": "芯片", "representative_seat": "机构专用", "top_trader": "机构资金", "reason": "连续三个交易日内涨幅偏离值累计达到30%", "three_day": True},
            {"code": "600001", "name": "丙", "net_amount": 60_000_000, "concept": "医药", "representative_seat": "某证券营业部", "top_trader": "未可靠识别", "reason": "日换手率达到20%的前5只证券", "three_day": False},
            {"code": "002001", "name": "丁", "net_amount": 40_000_000, "concept": "芯片", "representative_seat": "深股通专用", "top_trader": "北向资金", "reason": "日涨幅偏离值达到7%的前5只证券", "three_day": False},
        ]
        conclusions = module.derive_conclusions(records)
        self.assertEqual("CLEAN_PASS", conclusions["status"])
        self.assertAlmostEqual(240_000_000 / 280_000_000, conclusions["metrics"]["top3_net_share"], places=6)
        self.assertEqual("芯片", conclusions["theme_focus"][0]["theme"])
        self.assertGreater(conclusions["theme_focus"][0]["allocated_net_amount"], conclusions["theme_focus"][1]["allocated_net_amount"])
        self.assertEqual("科技硬件", conclusions["direction_focus"][0]["direction"])
        self.assertEqual(3, conclusions["direction_focus"][0]["stock_count"])
        self.assertAlmostEqual(220_000_000 / 280_000_000, conclusions["direction_focus"][0]["share_of_all"], places=6)
        self.assertEqual(
            {"capital_concentration", "capital_focus", "seat_style", "board_style", "persistence", "trigger_style", "risk_boundary"},
            {section["key"] for section in conclusions["sections"]},
        )
        for section in conclusions["sections"]:
            self.assertTrue(section["conclusion"].strip())
            self.assertTrue(section["evidence"])
            self.assertTrue(section["confidence"] in {"HIGH", "MEDIUM", "LOW"})

    def test_business_numbers_use_half_even_quantization_to_12_places(self):
        module = load_workflow()
        self.assertTrue(hasattr(module, "quantize_business_float"))
        self.assertEqual(0.123456789012, module.quantize_business_float("0.1234567890125"))
        self.assertEqual(0.123456789014, module.quantize_business_float("0.1234567890135"))
        with self.assertRaisesRegex(ValueError, "invalid_business_number"):
            module.quantize_business_float("invalid")
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "non_finite_business_number"):
                module.quantize_business_float(value)

        records = [
            {"code": "300001", "name": "甲", "net_amount": 100_000_000, "concept": "芯片、算力", "top_trader": "北向资金", "reason": "日涨幅达到15%的前5只证券", "three_day": False},
            {"code": "688001", "name": "乙", "net_amount": 80_000_000, "concept": "芯片", "top_trader": "机构资金", "reason": "连续三个交易日内涨幅偏离值累计达到30%", "three_day": True},
            {"code": "600001", "name": "丙", "net_amount": 60_000_000, "concept": "医药", "top_trader": "普通营业部", "reason": "日换手率达到20%的前5只证券", "three_day": False},
            {"code": "002001", "name": "丁", "net_amount": 40_000_000, "concept": "芯片", "top_trader": "北向资金", "reason": "日涨幅偏离值达到7%的前5只证券", "three_day": False},
        ]
        conclusions = module.derive_conclusions(records)
        self.assertEqual(0.857142857143, conclusions["metrics"]["top3_net_share"])

        def assert_quantized(value):
            if isinstance(value, dict):
                for child in value.values():
                    assert_quantized(child)
            elif isinstance(value, list):
                for child in value:
                    assert_quantized(child)
            elif isinstance(value, Decimal):
                self.fail(f"Decimal leaked into business JSON: {value}")
            elif isinstance(value, float):
                expected = Decimal(str(value)).quantize(
                    Decimal("0.000000000001"),
                    rounding=ROUND_HALF_EVEN,
                )
                self.assertEqual(Decimal(str(value)), expected)

        assert_quantized(conclusions)
        json.dumps(conclusions, ensure_ascii=False, allow_nan=False)

    def test_decimal_sum_is_stable_for_python_311_and_313(self):
        module = load_workflow()
        records = [
            {
                "code": f"300{index:03d}",
                "name": f"样本{index}",
                "net_amount": 0.1,
                "concept": "芯片",
                "top_trader": "北向资金",
                "reason": "日涨幅达到15%的前5只证券",
                "three_day": False,
            }
            for index in range(10)
        ]
        conclusions = module.derive_conclusions(records)
        self.assertEqual(1.0, conclusions["metrics"]["total_net_amount"])
        self.assertEqual(1.0, conclusions["metrics"]["theme_coverage_share"])
        self.assertEqual(1.0, conclusions["direction_focus"][0]["share_of_all"])

    def test_data_only_payload_is_rejected_and_report_leads_with_conclusions(self):
        module = load_workflow()
        data_only = {"schema": "A_SHARE_LONGHUBANG_ANALYSIS_V1", "status": "CLEAN_PASS", "trade_date": "2026-08-17", "threshold_yuan": 50_000_000, "stock_count": 1, "stocks": [{"code": "300001"}]}
        with self.assertRaisesRegex(ValueError, "analysis_conclusions_missing"):
            module.validate_analysis_payload(data_only)

        records = [{"code": "300001", "name": "甲", "net_amount": 100_000_000, "concept": "芯片", "representative_seat": "深股通专用", "top_trader": "北向资金", "reason": "日涨幅达到15%的前5只证券", "three_day": False}]
        payload = {**data_only, "stock_count": 1, "stocks": records, "conclusions": module.derive_conclusions(records)}
        module.validate_analysis_payload(payload)
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            module.write_report(payload, report)
            text = report.read_text(encoding="utf-8")
        self.assertLess(text.index("## 核心结论"), text.index("| 股票 |"))
        self.assertIn("证据：", text)
        self.assertNotIn("结论：榜单资金集中度按净买额降序展示", text)

    def test_shortline_client_command_passes_two_datasets_as_an_array(self):
        module = load_workflow()
        command = module.duanxianxia_command(Path(r"C:\temp\dxx.json"))
        self.assertIn("@('hotlist','ztplate')", command[3])
        self.assertNotEqual(["-Dataset", "hotlist", "ztplate"], command[-3:])

    def test_price_limit_wording_is_classified_by_actual_rise_trigger(self):
        module = load_workflow()
        record = {"reason": "有价格涨跌幅限制的日收盘价格涨幅偏离值达到7%的前五只证券", "three_day": False}
        self.assertEqual("上涨偏离", module.trigger_group(record))

    def test_poster_builder_rejects_missing_conclusion_binding(self):
        load_workflow()
        poster_builder = load_poster_builder()
        with self.assertRaisesRegex(ValueError, "poster_conclusions_missing"):
            poster_builder.validate_conclusions({})

    def test_poster_wrap_preserves_complete_words_and_rejects_truncation(self):
        load_workflow()
        poster_builder = load_poster_builder()
        self.assertEqual(["通信技术、", "DeepSeek概念"], poster_builder.wrap("通信技术、DeepSeek概念", 11))
        self.assertEqual("普通营业部\n名录无精确匹配", poster_builder.poster_trader_label("普通营业部（公开游资名录无精确匹配）"))
        with self.assertRaisesRegex(ValueError, "poster_text_overflow"):
            poster_builder.wrap("甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉", 4, max_lines=2)

    def test_poster_paginates_for_exact_1080_width_readability(self):
        poster_builder = load_poster_builder()
        self.assertEqual((1080, 608), poster_builder.PREVIEW)
        self.assertEqual(9, poster_builder.PAGE_SIZE)
        self.assertEqual(2, max((17 + poster_builder.PAGE_SIZE - 1) // poster_builder.PAGE_SIZE, (7 + poster_builder.CONCLUSIONS_PER_PAGE - 1) // poster_builder.CONCLUSIONS_PER_PAGE))
        self.assertEqual([[1, 2], [3], [4], [5]], poster_builder.balanced_chunks([1, 2, 3, 4, 5], 4))
        scale = poster_builder.WIDTH / poster_builder.PREVIEW[0]
        self.assertGreaterEqual(poster_builder.POLICY["body_source_font_px"] / scale, 32)
        self.assertGreaterEqual(poster_builder.POLICY["heading_source_font_px"] / scale, 45)
        self.assertGreaterEqual(poster_builder.POLICY["min_source_font_px"] / scale, 22)

    def test_poster_validator_rejects_data_only_audit(self):
        load_workflow()
        poster_validator = load_poster_validator()
        with tempfile.TemporaryDirectory() as temporary:
            poster = Path(temporary) / "poster.png"
            Image.new("RGB", (16, 16), "white").save(poster)
            errors = poster_validator.validate(poster, {"policy": poster_validator.POLICY, "stock_count": 1, "visible_stock_count": 1, "pages": []})
        self.assertIn("poster_analysis_binding_invalid", errors)
        self.assertIn("poster_conclusion_coverage_invalid", errors)

    def test_analysis_rejects_placeholder_concepts_and_trader_attribution(self):
        module = load_workflow()
        clean_records = [{"code": "300001", "name": "甲", "net_amount": 100_000_000, "concept": "通信技术", "representative_seat": "深股通专用", "top_trader": "北向交易通道", "reason": "日涨幅达到15%的前5只证券", "three_day": False}]
        payload = {
            "schema": "A_SHARE_LONGHUBANG_ANALYSIS_V1",
            "status": "CLEAN_PASS",
            "trade_date": "2026-08-18",
            "threshold_yuan": 50_000_000,
            "stock_count": 1,
            "stocks": [{**clean_records[0], "concept": "其他", "top_trader": "未可靠识别"}],
            "conclusions": module.derive_conclusions(clean_records),
        }
        with self.assertRaisesRegex(ValueError, "analysis_placeholder_text_forbidden"):
            module.validate_analysis_payload(payload)

    def test_public_seat_catalog_uses_exact_normalized_matches(self):
        module = load_workflow()
        profiles = [{"name": "徐留胜", "seats": ["华泰证券股份有限公司深圳益田路荣超商务中心证券营业部"], "evidence": "市场公开归因"}]
        public_seats = [{"name": "国泰海通证券三亚迎宾路", "url": "https://lianban.net/xiwei/cfeead62d4.html"}, {"name": "国盛证券上海浦东新区世纪大道", "url": "https://lianban.net/xiwei/928fc1ccd6.html"}]
        catalog = module.build_seat_catalog(profiles, public_seats)
        named = module.attribute_seat("华泰证券股份有限公司深圳益田路荣超商务中心证券营业部", catalog)
        active = module.attribute_seat("国泰海通证券股份有限公司三亚迎宾路证券营业部", catalog)
        unrelated = module.attribute_seat("高盛(中国)证券有限责任公司上海浦东新区世纪大道证券营业部", catalog)
        self.assertEqual(("named_trader", "徐留胜"), (named["category"], named["label"]))
        self.assertEqual(("public_active_seat", "国泰海通证券三亚迎宾路"), (active["category"], active["label"]))
        self.assertEqual("ordinary_brokerage", unrelated["category"])
        self.assertNotEqual("国盛证券上海浦东新区世纪大道", unrelated["label"])

    def test_public_trader_scan_checks_every_seat_not_only_top_net_seat(self):
        module = load_workflow()
        catalog = module.build_seat_catalog(
            [{"name": "徐留胜", "seats": ["华泰证券股份有限公司深圳益田路荣超商务中心证券营业部"], "evidence": "市场公开归因"}],
            [],
        )
        seats = [
            {"name": "某证券股份有限公司普通路证券营业部", "buy": 90_000_000, "sell": 0, "net": 90_000_000},
            {"name": "华泰证券股份有限公司深圳益田路荣超商务中心证券营业部", "buy": 40_000_000, "sell": 0, "net": 40_000_000},
        ]
        result = module.summarize_seat_attribution(seats, catalog)
        self.assertIn("普通路证券营业部", result["representative_seat"])
        self.assertEqual("徐留胜", result["top_trader"])
        self.assertEqual(1, len(result["public_trader_matches"]))
        no_match = module.summarize_seat_attribution([{"name": "机构专用", "buy": 20_000_000, "sell": 0, "net": 20_000_000}], catalog)
        self.assertEqual("本股榜单无公开游资名录席位", no_match["top_trader"])

    def test_lianban_seat_card_parser_excludes_activity_statistics(self):
        module = load_workflow()
        parser = module._SeatIndexParser()
        parser.feed('<a class="tci" href="/xiwei/cfeead62d4.html"><b>国泰海通证券三亚迎宾路</b><span>上榜45日 · 买入6.4亿 · 净-0.1亿</span></a>')
        self.assertEqual("国泰海通证券三亚迎宾路", parser.items[0]["name"])

    def test_representative_public_seat_has_priority_without_overstating_seat_style(self):
        module = load_workflow()
        catalog = module.build_seat_catalog(
            [{"name": "思明南路", "seats": ["东亚前海证券有限责任公司上海分公司"]}],
            [{"name": "国泰海通证券三亚迎宾路", "url": "https://lianban.net/xiwei/cfeead62d4.html"}],
        )
        result = module.summarize_seat_attribution([
            {"name": "国泰海通证券股份有限公司三亚迎宾路证券营业部", "buy": 90_000_000, "sell": 0, "net": 90_000_000},
            {"name": "东亚前海证券有限责任公司上海分公司", "buy": 40_000_000, "sell": 0, "net": 40_000_000},
        ], catalog)
        self.assertEqual("国泰海通证券三亚迎宾路", result["top_trader"])
        self.assertEqual("public_active_seat", result["seat_category"])
        self.assertEqual(2, len(result["public_trader_matches"]))

    def test_seat_style_uses_representative_type_not_another_public_match(self):
        module = load_workflow()
        records = [{"code": "300001", "name": "甲", "net_amount": 100_000_000, "concept": "通信技术", "representative_seat": "普通营业部", "top_trader": "徐留胜", "seat_category": "ordinary_brokerage", "reason": "日换手率达到20%的前5只证券", "three_day": False}]
        conclusions = module.derive_conclusions(records)
        self.assertEqual("普通营业部", conclusions["seat_structure"][0]["name"])

    def test_official_precise_concepts_replace_generic_fallbacks(self):
        module = load_workflow()
        payload = {"ssbk": [
            {"BOARD_NAME": "电子", "IS_PRECISE": None, "BOARD_RANK": 1},
            {"BOARD_NAME": "题材股", "IS_PRECISE": None, "BOARD_RANK": 2},
            {"BOARD_NAME": "通信技术", "IS_PRECISE": "1", "BOARD_RANK": 20},
            {"BOARD_NAME": "液冷服务器", "IS_PRECISE": "1", "BOARD_RANK": 23},
        ], "hxtc": [{"KEY_CLASSIF": "主营业务", "KEYWORD": "热管理材料"}]}
        evidence = module.extract_official_concepts(payload)
        self.assertEqual(["通信技术", "液冷服务器"], evidence["precise_concepts"])
        self.assertNotIn("题材股", evidence["concepts"])
        self.assertNotEqual("其他主题", module.direction_for_theme("股权转让"))

if __name__ == "__main__": unittest.main(verbosity=2)
