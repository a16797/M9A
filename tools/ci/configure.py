import shutil
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
common_assets_dir = root_dir / "MaaCommonAssets"
resource_dir = root_dir / "resource"


def configure_ocr_model():
    shutil.copytree(
        common_assets_dir / "OCR" / "ppocr_v4" / "zh_cn",
        resource_dir / "base" / "model" / "ocr",
        dirs_exist_ok=True,
    )


if __name__ == "__main__":
    configure_ocr_model()
