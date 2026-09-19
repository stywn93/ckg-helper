import os
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

DEFAULT_COMBINED_WORKBOOK_NAME = "ckg_data.xlsx"

SHEET_ALIASES = {
    "pendaftaran_umum": ["pendaftaran_umum", "pendaftaran umum", "pendaftaran"],
    "konfirm_kehadiran": ["konfirm_kehadiran", "konfirmasi_kehadiran", "konfirm kehadiran", "konfirmasi kehadiran"],
    "anak": ["anak"],
    "remaja": ["remaja"],
    "dewasa": ["dewasa"],
    "lansia": ["lansia"],
    "pendaftaran_sekolah": ["pendaftaran_sekolah", "pendaftaran sekolah"],
    "konfirm_kehadiran_sekolah": [
        "konfirm_kehadiran_sekolah",
        "konfirmasi_kehadiran_sekolah",
        "konfirm kehadiran sekolah",
        "konfirmasi kehadiran sekolah",
    ],
    "pelayanan_sekolah": ["pelayanan_sekolah", "pelayanan sekolah"],
}


def normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def find_matching_sheet(sheetnames: list[str], target_key: str) -> str | None:
    norm_target = normalize_name(target_key)
    valid_aliases = [normalize_name(a) for a in SHEET_ALIASES.get(norm_target, [norm_target])]
    for s in sheetnames:
        if normalize_name(s) in valid_aliases:
            return s
    return None


def format_cell_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def resolve_dataset(
    dataset_key: str,
    preferred_sheet: str | None = None,
    project_root: Path | None = None,
) -> tuple[Path, str | None]:
    """
    Returns (path_to_file, sheet_name_or_none).
    1. Checks if dataset/ckg_data.xlsx exists and has matching sheet.
    2. Else falls back to standalone dataset/<dataset_key>.xlsx.
    """
    if project_root is None:
        project_root = Path(os.getenv("CKG_PROJECT_ROOT", Path.cwd()))

    dataset_dir = project_root / "dataset"
    combined_name = os.getenv("CKG_COMBINED_DATASET", DEFAULT_COMBINED_WORKBOOK_NAME)
    combined_path = dataset_dir / combined_name

    target_sheet = preferred_sheet or dataset_key

    if combined_path.exists():
        try:
            wb = load_workbook(str(combined_path), read_only=True)
            matched = find_matching_sheet(wb.sheetnames, target_sheet)
            wb.close()
            if matched:
                return combined_path, matched
        except Exception:
            pass

    standalone_path = dataset_dir / f"{dataset_key}.xlsx"
    return standalone_path, None


class ExcelStatusWorkbook:
    def __init__(self, path: str | Path, sheet_name: str | None = None, status_column: str = "status"):
        self.path = Path(path)
        self.status_column = status_column
        self.workbook = load_workbook(str(self.path))
        self.sheet_name = sheet_name

        if sheet_name:
            matched_sheet = find_matching_sheet(self.workbook.sheetnames, sheet_name)
            if not matched_sheet:
                available = ", ".join(repr(s) for s in self.workbook.sheetnames)
                raise ValueError(
                    f"Sheet '{sheet_name}' tidak ditemukan di {self.path.name}. "
                    f"Sheet yang tersedia: [{available}]"
                )
            self.sheet = self.workbook[matched_sheet]
        else:
            self.sheet = self.workbook.active

        self.headers = [cell.value for cell in self.sheet[1]]
        self._ensure_status_column()
        self.summary = {
            "empty_rows": 0,
            "skipped_rows": [],
            "total_data_rows": self.sheet.max_row - 1,
        }

    def _ensure_status_column(self) -> None:
        if self.status_column not in self.headers:
            self.sheet.cell(row=1, column=len(self.headers) + 1, value=self.status_column)
            self.headers.append(self.status_column)

    def pending_rows(self) -> list[dict]:
        rows = []
        self.summary["empty_rows"] = 0
        self.summary["skipped_rows"] = []

        for row_number, row in enumerate(self.sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                self.summary["empty_rows"] += 1
                continue

            data = dict(zip(self.headers, row))
            status = str(data.get(self.status_column)).strip().upper()
            if status in ["SUCCESS", "PASIEN INI SUDAH MENERIMA CKG"]:
                self.summary["skipped_rows"].append(row_number)
                continue

            rows.append({"row_number": row_number, "data": data})

        return rows

    def update_status(self, row_number: int, status: str) -> None:
        column_index = self.headers.index(self.status_column) + 1
        self.sheet.cell(row=row_number, column=column_index, value=status)
        self.workbook.save(str(self.path))

    def append_row_to_dataset(self, target_dataset_key: str, data: dict) -> None:
        """
        Appends to target sheet using the SAME openpyxl instance in combined mode
        (preventing in-memory overwrite collisions), or falls back to standalone file.
        """
        matched_sheet = find_matching_sheet(self.workbook.sheetnames, target_dataset_key)
        if matched_sheet:
            dest_sheet = self.workbook[matched_sheet]
            headers = [cell.value for cell in dest_sheet[1]]

            first_empty_row = None
            for row in dest_sheet.iter_rows(min_row=2, max_col=1, values_only=False):
                if row[0].value is None:
                    first_empty_row = row[0].row
                    break
            if first_empty_row is None:
                first_empty_row = dest_sheet.max_row + 1

            for key, value in data.items():
                if key in headers:
                    col_index = headers.index(key) + 1
                    dest_sheet.cell(row=first_empty_row, column=col_index, value=value)

            self.workbook.save(str(self.path))
        else:
            target_path = self.path.parent / f"{target_dataset_key}.xlsx"
            if not target_path.exists():
                return
            append_wb = ExcelAppendWorkbook(target_path)
            append_wb.append_row(data)


class ExcelAppendWorkbook:
    def __init__(self, path: str | Path, sheet_name: str | None = None):
        self.path = Path(path)
        self.workbook = load_workbook(str(self.path))
        if sheet_name:
            matched_sheet = find_matching_sheet(self.workbook.sheetnames, sheet_name)
            if not matched_sheet:
                self.sheet = self.workbook.create_sheet(title=sheet_name)
            else:
                self.sheet = self.workbook[matched_sheet]
        else:
            self.sheet: Worksheet = self.workbook.active
        self.headers = [cell.value for cell in self.sheet[1]]

    def _first_empty_row(self) -> int:
        for row in self.sheet.iter_rows(min_row=2, max_col=1, values_only=False):
            if row[0].value is None:
                return row[0].row
        return self.sheet.max_row + 1

    def append_row(self, data: dict) -> None:
        row_number = self._first_empty_row()
        for key, value in data.items():
            if key in self.headers:
                col_index = self.headers.index(key) + 1
                self.sheet.cell(row=row_number, column=col_index, value=value)
        self.workbook.save(str(self.path))
