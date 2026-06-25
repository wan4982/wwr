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
    api_key = (
        os.getenv("ZHIPUAI_API_KEY")
        or os.getenv("ZHIPU_API_KEY")
        or os.getenv("GLM_API_KEY")
        or ""
    ).strip()
    model = os.getenv("GLM_MODEL", "glm-4-flash").strip()
    base_url = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/").strip()
    if not api_key:
        print("未检测到 ZHIPUAI_API_KEY。")
        raise SystemExit(1)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "只回复：连接成功"}],
            temperature=0,
            max_tokens=20,
            timeout=25,
        )
        print("智谱AI（GLM）API 连接成功。")
        print(response.choices[0].message.content)
    except Exception as exc:
        print("智谱AI（GLM）API 连接失败。")
        print(f"错误类型：{type(exc).__name__}")
        print(f"错误信息：{exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
