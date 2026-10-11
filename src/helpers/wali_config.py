import os
from pathlib import Path

WALI_ENV_KEYS = {
    "WALI_NIK": "NIK Wali",
    "WALI_NAMA": "Nama Lengkap Wali",
    "WALI_TGL_LAHIR": "Tanggal Lahir Wali (YYYY-MM-DD)",
    "WALI_GENDER": "Jenis Kelamin Wali (Laki-laki/Perempuan)",
}

FALLBACK_WALI_MAP = {
    "nik_wali": "WALI_NIK",
    "nama_wali": "WALI_NAMA",
    "tgl_lahir_wali": "WALI_TGL_LAHIR",
    "gender_wali": "WALI_GENDER",
}

DEFAULT_PERNIKAHAN_FALLBACK = "Belum Menikah"
DEFAULT_PEKERJAAN_FALLBACK = "Lainnya"


def is_empty_value(val) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.lower() in ("none", "nan")


def get_wali_config() -> dict[str, str]:
    return {key: os.getenv(key, "").strip() for key in WALI_ENV_KEYS}


def is_wali_config_complete(config: dict[str, str] | None = None) -> bool:
    cfg = config if config is not None else get_wali_config()
    return all(bool(cfg.get(key, "").strip()) for key in WALI_ENV_KEYS)


def save_wali_config_to_env(env_path: Path, config: dict[str, str]) -> None:
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        matched = False
        for key, val in config.items():
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={val}")
                updated_keys.add(key)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    missing_keys = [k for k in config if k not in updated_keys]
    if missing_keys:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append("# Konfigurasi Data Wali (Fallback)")
        for k in missing_keys:
            new_lines.append(f"{k}={config[k]}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    for k, v in config.items():
        os.environ[k] = v


def ensure_wali_credentials(app_root: Path) -> dict[str, str]:
    env_path = app_root / ".env"
    config = get_wali_config()
    if is_wali_config_complete(config):
        return config

    print("\nKonfigurasi data wali belum lengkap di file .env.")
    print("Masukkan data wali (digunakan sebagai fallback jika kolom di Excel kosong):")

    for key, label in WALI_ENV_KEYS.items():
        val = config.get(key, "").strip()
        while not val:
            val = input(f"{label}: ").strip()
        config[key] = val

    save_wali_config_to_env(env_path, config)
    print("Konfigurasi data wali berhasil disimpan ke .env.\n")
    return config


def apply_wali_fallback(data: dict, wali_config: dict[str, str] | None = None) -> dict:
    """
    Mengisi data yang kosong:
    - Data wali (nik_wali, nama_wali, tgl_lahir_wali, gender_wali) dari wali_config
    - Data peserta:
      - pernikahan: fallback 'Belum Menikah'
      - pekerjaan: fallback 'Lainnya'
      - no_whatsapp_wali: fallback dari no_whatsapp peserta
    """
    cfg = wali_config if wali_config is not None else get_wali_config()
    filled = dict(data)

    # Fallback kolom wali dari konfigurasi .env
    for field, env_key in FALLBACK_WALI_MAP.items():
        if is_empty_value(filled.get(field)):
            fallback_val = cfg.get(env_key, "").strip()
            if fallback_val:
                filled[field] = fallback_val

    # Fallback status pernikahan peserta
    if is_empty_value(filled.get("pernikahan")):
        filled["pernikahan"] = DEFAULT_PERNIKAHAN_FALLBACK

    # Fallback pekerjaan peserta
    if is_empty_value(filled.get("pekerjaan")):
        filled["pekerjaan"] = DEFAULT_PEKERJAAN_FALLBACK

    # Fallback no_whatsapp_wali ke no_whatsapp pasien jika kosong
    if is_empty_value(filled.get("no_whatsapp_wali")):
        patient_wa = filled.get("no_whatsapp")
        if not is_empty_value(patient_wa):
            filled["no_whatsapp_wali"] = patient_wa

    return filled
