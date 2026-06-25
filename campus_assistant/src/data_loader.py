from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .config import DATA_FILE


@dataclass(frozen=True)
class CampusRecord:
    id: int
    category: str
    question: str
    answer: str
    source: str

    @property
    def searchable_text(self) -> str:
        return f"{self.category} {self.question} {self.answer} {self.source}"

# 读取校园知识库
def load_records(path: Path = DATA_FILE) -> list[CampusRecord]:
    records: list[CampusRecord] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            records.append(
                CampusRecord(
                    id=int(row["id"]),
                    category=row["category"].strip(),
                    question=row["question"].strip(),
                    answer=row["answer"].strip(),
                    source=row["source"].strip(),
                )
            )
    return records
