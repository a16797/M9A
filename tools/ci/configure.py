from pathlib import Path

import shutil

assets_dir = Path(__file__).parent.parent.parent / "assets"


def configure_ocr_model():
    # PP-OCRv6 混合组合：det 用 small 档，rec + keys 用 tiny 档
    ocr_root = assets_dir / "MaaCommonAssets" / "OCR" / "ppocr_v6"
    target = assets_dir / "resource" / "base" / "model" / "ocr"
    target.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ocr_root / "small" / "det.onnx", target / "det.onnx")
    shutil.copy2(ocr_root / "tiny" / "rec.onnx", target / "rec.onnx")
    shutil.copy2(ocr_root / "tiny" / "keys.txt", target / "keys.txt")
    # README 准确描述混合组合：det 来自 small 档，rec 来自 tiny 档
    (target / "README.md").write_text(
        "# OCR 模型\n\n"
        "PP-OCRv6 混合组合：\n\n"
        "- det：PP-OCRv6_small_det（small 档文本检测模型）\n"
        "- rec：PP-OCRv6_tiny_rec（tiny 档文本识别模型，"
        "支持简体中文、繁体中文、英文及 46 种拉丁语系语言，不含日文）\n\n"
        "from <https://www.paddleocr.ai/main/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html>\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    configure_ocr_model()
