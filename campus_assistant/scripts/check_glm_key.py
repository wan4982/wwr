from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import BASE_DIR


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    key = (
        os.getenv("ZHIPUAI_API_KEY")
        or os.getenv("ZHIPU_API_KEY")
        or os.getenv("GLM_API_KEY")
        or ""
    ).strip()
    model = os.getenv("GLM_MODEL", "glm-4-flash")
    if not key:
        print("未检测到 ZHIPUAI_API_KEY。请在项目根目录 .env 中配置。")
        raise SystemExit(1)
    if len(key) < 20:
        print("检测到 ZHIPUAI_API_KEY，但长度看起来不完整，请确认是否复制完整。")
        raise SystemExit(1)
    print(f"已检测到智谱AI Key：***{key[-4:]}")
    print(f"当前模型：{model}")


if __name__ == "__main__":
    main()
