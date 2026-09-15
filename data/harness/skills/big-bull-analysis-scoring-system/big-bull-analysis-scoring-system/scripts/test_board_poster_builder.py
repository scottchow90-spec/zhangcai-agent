from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from pathlib import Path

from PIL import Image, ImageStat

from poster_builder import render_poster


def board_payload(count: int = 20) -> dict:
    rows = []
    for index in range(count):
        rows.append(
            {
                "rank": index + 1,
                "name": f"测试股票{index + 1:02d}",
                "symbol": f"60{index:04d}.SH",
                "score": 90 - index,
                "eligible": index < 3,
                "signal_source": "日线核对",
                "hard_reasons": [] if index < 3 else ["上方阻挡近"],
                "components": {
                    "方向位置": 23,
                    "上涨劲头": 22,
                    "当天表现": 18,
                    "上下空间": 17,
                    "额外提醒": 2,
                },
            }
        )
    return {
        "rows": rows,
        "board": {
            "name": "测试板块",
            "constituent_count": count,
            "updated_at_text": "2026年08月17日19时41分48秒",
        },
        "score_date": "20260817",
    }


def test_board_poster_contains_every_constituent_with_preview(tmp_path: Path) -> None:
    output = tmp_path / "poster.png"

    validation = render_poster(board_payload(), output)

    assert validation["poster_row_count"] == 20
    assert validation["expected_poster_row_count"] == 20
    assert validation["board_constituent_count"] == 20
    assert validation["minimum_font_px"] >= 96
    assert validation["minimum_preview_font_px"] >= 24
    assert Path(validation["preview_path"]).is_file()
    with Image.open(validation["preview_path"]) as preview:
        assert preview.size == (1920, 1080)


def test_board_poster_corners_pass_light_background_gate(tmp_path: Path) -> None:
    output = tmp_path / "poster.png"

    render_poster(board_payload(), output)

    with Image.open(output) as image:
        corners = (
            image.crop((0, 0, 384, 216)),
            image.crop((7296, 0, 7680, 216)),
            image.crop((0, 4104, 384, 4320)),
            image.crop((7296, 4104, 7680, 4320)),
        )
        luminance = [sum(ImageStat.Stat(corner).mean[:3]) / 3.0 for corner in corners]
    assert min(luminance) >= 230.0
