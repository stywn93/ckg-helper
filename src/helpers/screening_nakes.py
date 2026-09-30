import re

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _is_locator(value):
    return hasattr(value, "count") and hasattr(value, "click")


def _unwrap(value):
    return value._locator if isinstance(value, _LoggingLocator) else value


class _LoggingLocator:
    def __init__(self, locator):
        self._locator = locator

    def __getattr__(self, name):
        attribute = getattr(self._locator, name)
        if name in {"click", "fill", "press", "press_sequentially", "set_checked", "type"}:
            def action(*args, **kwargs):
                if self._locator.count() == 0:
                    action_label = {
                        "click": "memilih data",
                        "fill": "mengisi data",
                        "press": "menekan tombol",
                        "press_sequentially": "mengisi data",
                        "set_checked": "mengubah pilihan",
                        "type": "mengetik data",
                    }.get(name, "menjalankan proses")
                    print(f"[PERINGATAN] Bagian formulir belum ditemukan saat {action_label}.")
                return attribute(*args, **kwargs)

            return action

        if callable(attribute):
            def call(*args, **kwargs):
                result = attribute(
                    *[_unwrap(arg) for arg in args],
                    **{key: _unwrap(value) for key, value in kwargs.items()},
                )
                return _LoggingLocator(result) if _is_locator(result) else result

            return call

        return _LoggingLocator(attribute) if _is_locator(attribute) else attribute


class _LoggingPage:
    def __init__(self, page):
        self._page = page

    def __getattr__(self, name):
        attribute = getattr(self._page, name)
        if callable(attribute):
            def call(*args, **kwargs):
                result = attribute(
                    *[_unwrap(arg) for arg in args],
                    **{key: _unwrap(value) for key, value in kwargs.items()},
                )
                return _LoggingLocator(result) if _is_locator(result) else result

            return call
        return _LoggingLocator(attribute) if _is_locator(attribute) else attribute

class ScreeningNakes:
    _SCREENING_KEYS = {
        "do_pertumbuhan_balita": "skrining_pertumbuhan",
        "do_kpsp": "skrining_kpsp",
        "do_m_chat_1": "skrining_m_chat_1",
        "do_m_chat_2": "skrining_m_chat_2",
        "do_risiko_tb_anak": "skrining_risiko_tb_anak",
        "do_tb_anak": "skrining_tb_anak",
        "do_riwayat_imunisasi_hepatitis_b": "skrining_imunisasi_hepatitis_b",
        "do_berat_lahir": "skrining_berat_lahir",
        "do_jantung_bawaan": "skrining_jantung_bawaan",
        "do_shk": "skrining_shk",
        "do_gizi_anak_sekolah": "skrining_gizi_anak_sekolah",
        "do_tekanan_darah_anak_remaja": "skrining_tekanan_darah_anak_remaja",
        "do_gula_darah_anak": "skrining_gula_darah_anak",
        "do_telinga_mata_anak_sekolah": "skrining_telinga_mata_anak_sekolah",
        "do_hepatitis_b_7_12": "skrining_hepatitis_b_7_12",
        "do_rdt_malaria": "skrining_rdt_malaria",
        "do_darah_tumit": "skrining_darah_tumit",
        "do_konfirmasi_shk": "skrining_konfirmasi_shk",
        "do_warna_kulit_dan_tinja": "skrining_warna_kulit_dan_tinja",
        "do_hasil_kramer": "skrining_hasil_kramer",
        "do_warna_kulit_dan_tinja_28": "skrining_warna_kulit_dan_tinja_28",
        "do_telinga_mata_anak": "skrining_telinga_mata_anak",
        "do_periksa_gigi_anak": "skrining_periksa_gigi_anak",
        "do_gizi_laki": "skrining_gizi",
        "do_gizi_perempuan": "skrining_gizi",
        "do_skilas_penurunan_kognitif": "skrining_skilas_penurunan_kognitif",
        "do_skilas_mobilisasi": "skrining_skilas_mobilisasi",
        "do_skilas_malnutrisi": "skrining_skilas_malnutrisi",
        "do_skilas_depresi": "skrining_skilas_depresi",
        "do_gangguan_fungsional": "skrining_gangguan_fungsional",
        "do_mini_cog": "skrining_mini_cog",
        "do_ad8_ina": "skrining_ad8_ina",
        "do_mobilisasi_lanjutan": "skrining_mobilisasi_lanjutan",
        "do_malnutrisi_lanjutan": "skrining_malnutrisi_lanjutan",
        "do_depresi_lanjutan": "skrining_depresi_lanjutan",
        "do_gula_darah_dewasa": "skrining_gula_darah_dewasa",
        "do_tekanan_darah_dewasa": "skrining_tekanan_darah_dewasa",
        "do_telinga_mata_18_39": "skrining_telinga_mata",
        "do_risiko_tb": "skrining_risiko_tb",
        "do_tb": "skrining_tb",
        "do_frambusia": "skrining_frambusia",
        "do_kusta": "skrining_kusta",
        "do_skabies": "skrining_skabies",
        "do_telinga_mata": "skrining_telinga_mata",
        "do_karies": "skrining_karies",
        "do_periodontal": "skrining_periodontal",
        "do_ppok": "skrining_ppok",
        "do_kadar_co": "skrining_kadar_co",
        "do_lipid": "skrining_lipid",
        "do_fibrosis": "skrining_fibrosis",
        "do_hepatitis": "skrining_hepatitis",
        "do_fungsi_ginjal": "skrining_fungsi_ginjal",
        "do_fungsi_ginjal_perempuan": "skrining_fungsi_ginjal",
        "do_kerusakan_ginjal": "skrining_kerusakan_ginjal",
        "do_kanker_payudara": "skrining_kanker_payudara",
        "do_hpv_dna": "skrining_hpv_dna",
        "do_inspekulo_iva": "skrining_inspekulo_iva",
        "do_jantung": "skrining_jantung",
        "do_kanker_usus": "skrining_kanker_usus",
        "do_kanker_paru": "skrining_kanker_paru",
        "do_catin_perempuan": "skrining_catin_perempuan",
        "do_hiv": "skrining_hiv",
        "do_sifilis": "skrining_sifilis",
    }

    def __init__(self, page, formatter):
        self.page = _LoggingPage(page)
        self.formatter = formatter
        self._detail_number = 1

    def _start_screening(self, title: str) -> None:
        self._detail_number = 1
        print(f"{Colors.OKBLUE}-- Menjalankan {title}{Colors.ENDC}")

    def _finish_screening(self) -> None:
        print()

    def _value(self, data: dict, key: str) -> str:
        value = self.formatter(data.get(key))
        label = key.replace("_", " ").capitalize()
        print(f"{self._detail_number}. {label}: {value}")
        self._detail_number += 1
        return value

    def _should_run(self, data:dict, key: str) -> bool:
        value = self.formatter(data.get(key))
        if value is None or str(value).strip() == "":
            return False
        return value == "Ya"

    def required(self, data: dict, key: str) -> str:
        value = self._value(data, key)
        if value is None or str(value).strip() == "":
            raise ValueError(f"kolom {key} tidak boleh kosong")
        if key == "tinggi_badan":
            value = re.sub(r"\s*cm\s*$", "", str(value), flags=re.IGNORECASE).strip()
            if not re.fullmatch(r"\d+(?:[.,]\d+)?", value):
                raise ValueError(f"kolom {key} harus berupa angka, contoh: 155")
            value = value.replace(",", ".")
        return value

    def do_pertumbuhan_balita(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_pertumbuhan_balita"]):
            print("Skrining Pertumbuhan Balita Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Pertumbuhan Balita dan Anak Pra Sekolah")
        self.page.locator('[id="rowfrm000016"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "posisi_pengukuran")).click()
        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "status_lingkar_kepala")).click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kpsp(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kpsp"]):
            print("Skrining KPSP Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining KPSP")
        self.page.locator('[id="rowfrm000017"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "hasil_kpsp")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_m_chat_1(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_m_chat_1"]):
            print("Skrining M Chat 1 Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining M CHAT 1")
        self.page.locator('[id="rowfrm000095"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "m_chat_1")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_m_chat_2(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_m_chat_2"]):
            print("Skrining M Chat 2 Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining M CHAT 2")
        self.page.locator('[id="rowfrm000019"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "m_chat_2"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_risiko_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb_anak"]):
            print("Skrining Risiko TB Anak Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Risiko TB")
        # do_pemeriksaan_check(page, "input#hasil-lab-1-0", True)
        self.page.locator('[id="rowfrm000175"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_batuk_tidak_sembuh")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "bb_turun")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "demam_hilang_timbul")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "lesu")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "pembesaran_getah_bening")
        ).click()
        radiografi_toraks = self.required(data, "radiografi_toraks")
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=radiografi_toraks
        ).click()
        if radiografi_toraks == "Ya":
            value = self.required(data, "hasil_rontgen")
            self.page.locator(
                "fieldset[aria-labelledby='sq_106_ariaTitle'] label"
            ).filter(
                has_text=re.compile(rf"^{re.escape(value)}$")
            ).click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_tb_anak"]):
            print("Skrining TB Anak Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining TB Anak")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-1-1']", True)
        self.page.locator('[id="rowfrm000178"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        kontak_tbc = self.required(data, "kontak_tbc")
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=kontak_tbc).click()
        if kontak_tbc == "Riwayat kontak serumah" or kontak_tbc == "Riwayat kontak erat":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_tbc")
            ).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        metode_pemeriksaan_tbc = self.required(data, "metode_pemeriksaan_tbc")
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=metode_pemeriksaan_tbc).click()
        if metode_pemeriksaan_tbc == "TCM":
            # print("TCM")
            self.page.locator("div#sq_103i.sd-input.sd-dropdown").click()
            self.page.locator("#sq_103i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif metode_pemeriksaan_tbc == "BTA":
            self.page.locator("div[aria-controls='sq_104i_list']").click()
            self.page.locator("#sq_104i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif metode_pemeriksaan_tbc == "NPOC":
            self.page.locator("div[aria-controls='sq_105i_list']").click()
            self.page.locator("#sq_105i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_riwayat_imunisasi_hepatitis_b(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_riwayat_imunisasi_hepatitis_b"]):
            print("Skrining Riwayat Imunisasi Hepatitis B Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Riwayat Hepatitis B")
        self.page.locator('[id="rowfrm000260"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "mendapat_imunisasi_hepatitis_b")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_berat_lahir(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do__berat_lahir"]):
            print("Skrining Berat Lahir Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Berat Lahir")
        self.page.locator('[id="rowfrm000010"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_lahir"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "berat_sekarang"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_jantung_bawaan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_jantung_bawaan"]):
            print("Skrining Jantung Bawaan Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Jantung Bawaan")
        self.page.locator('[id="rowfrm000011"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "pjb_tangan_kanan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "pjb_kaki"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_shk(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_shk"]):
            print("Skrining SHK Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining SHK")
        self.page.locator('[id="rowfrm000012"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "shk")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "g6pd")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "hak")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gizi_anak_sekolah(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gizi_anak_sekolah"]):
            print("Skrining Gizi Anak Sekolah Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Gizi Anak Sekolah")
        self.page.locator('[id="rowfrm000119"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_tekanan_darah_anak_remaja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_tekanan_darah_anak_remaja"]):
            print("Skrining Tekanan Darah Anak dan Remaja Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Tekanan Darah Anak dan Remaja")
        self.page.locator('[id="rowfrm000266"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "sistol"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "diastol"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gula_darah_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gula_darah_anak"]):
            print("Skrining Gula Darah Anak Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Gula Darah Anak")
        self.page.locator('[id="rowfrm000195"]').click()
        anak_pernah_diabetes = self.required(data, "anak_pernah_diabetes")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=anak_pernah_diabetes
        ).click()
        if anak_pernah_diabetes == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "berapa_bulan_diabetes"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "gds"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_telinga_mata_anak_sekolah(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_telinga_mata_anak_sekolah"]):
            print("Skrining Telinga Mata Anak Sekolah Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Telinga Mata Anak Sekolah")
        self.page.locator('[id="rowfrm000137"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "gangguan_pendengaran_kanan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "gangguan_pendengaran_kiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi_kanan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi_kiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "infeksi_telinga_kanan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "infeksi_telinga_kiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "selaput_mata_merah_kanan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "selaput_mata_merah_kiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_penglihatan_kanan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_109_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_penglihatan_kiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_110_ariaTitle'] label").filter(
            has_text=self.required(data, "menggunakan_kacamata")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_hepatitis_b_7_12(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hepatitis_b_7_12"]):
            print("Skrining Hepatitis B Usia 7-12 Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Hepatitis B Usia 7-12 Tahun")
        self.page.locator('[id="rowfrm000159"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hasil_hepatitis_b")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_rdt_malaria(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_rdt_malaria"]):
            print("Skrining RDT Malaria Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining RDT Malaria")
        self.page.locator('[id="rowfrm000117"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hasil_rdt_malaria")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_darah_tumit(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_darah_tumit"]):
            print("Skrining Darah Tumit Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Darah Tumit")
        self.page.locator('[id="rowfrm000082"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "darah_tumit")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_konfirmasi_shk(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_konfirmasi_shk"]):
            print("Skrining Konfirmasi SHK Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Konfirmasi SHK")
        self.page.locator('[id="rowfrm000083"]').click()
        dilakukan_konfirmasi_shk = self.required(data, "dilakukan_konfirmasi_shk")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=dilakukan_konfirmasi_shk
        ).click()
        if dilakukan_konfirmasi_shk == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_shk")
            ).click()
        dilakukan_konfirmasi_g6pd = self.required(data, "dilakukan_konfirmasi_g6pd")
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=dilakukan_konfirmasi_g6pd
        ).click()
        if dilakukan_konfirmasi_g6pd == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_g6pd")
            ).click()
        dilakukan_konfirmasi_hak = self.required(data, "dilakukan_konfirmasi_hak")
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=dilakukan_konfirmasi_hak
        ).click()
        if dilakukan_konfirmasi_hak == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_hak")
            ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_warna_kulit_dan_tinja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_warna_kulit_dan_tinja"]):
            print("Skrining Edukasi Warna Kulit dan Tinja Bayi Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Edukasi Warna Kulit dan Tinja Bayi")
        self.page.locator('[id="rowfrm000079"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "dilakukan_edukasi_warna_kulit_dan_tinja")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_hasil_kramer(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hasil_kramer"]):
            print("Skrining Hasil Kramer Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Hasil Kramer pada Bayi Kuning")
        self.page.locator('[id="rowfrm000240"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "nilai_hasil_kramer")).first.click()
        
        # self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        #     has_text=self.required(data, "nilai_hasil_kramer")
        # ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_warna_kulit_dan_tinja_28(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_warna_kulit_dan_tinja_28"]):
            print("Skrining Penilaian Warna Kulit dan Tinja 14 - 28 hari Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Penilaian Warna Kulit dan Tinja 14 - 28 hari")
        self.page.locator('[id="rowfrm000252"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "tgl_pemeriksaan_kramer"))

        self.page.locator("div#sq_101i.sd-input.sd-dropdown").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "kramer_bayi_kuning")).click()

        self.page.locator("div#sq_102i.sd-input.sd-dropdown").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "derajat_warna_tinja")).click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_telinga_mata_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_telinga_mata_anak"]):
            print("Skrining Telinga dan Mata Anak Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Telinga dan Mata Anak")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-3-0']", True)
        self.page.locator('[id="rowfrm000085"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "serumen_impaksi")).first.click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "infeksi_telinga")).first.click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "tes_daya_dengar")).first.click()
        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "selaput_mata_merah")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "pupil_putih")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_periksa_gigi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_periksa_gigi_anak"]):
            print("Skrining Pemeriksaan Gigi Anak Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Pemeriksaan Gigi Anak")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-3-0']", True)
        self.page.locator('[id="rowfrm000131"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "jumlah_gigi_karies")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gizi_laki(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gizi_laki"]):
            print("Skrining Gizi Laki Dilewati (Tidak Aktif)")
            return
        label = "Gizi (BB - TB - Lingkar Perut) Laki-laki"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Gizi Laki")
        self.page.locator('[id="rowfrm000093"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "lingkar_perut"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gizi_perempuan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gizi_perempuan"]):
            print("Skrining Gizi Perempuan Dilewati (Tidak Aktif)")
            return
        label = "Gizi (BB - TB - Lingkar Perut) Perempuan"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Gizi Perempuan")
        self.page.locator('[id="rowfrm000051"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "lingkar_perut"))
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_skilas_penurunan_kognitif(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skilas_penurunan_kognitif"]):
            print("Skrining Skilas Penurunan Kognitif Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining SKILAS Penurunan Kognitif")
        self.page.locator('[id="rowfrm000029"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "mengingat_3_kata")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "tanggal_berapa_dimana")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "ulangi_3_kata_sebelumnya")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_skilas_mobilisasi(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skilas_mobilisasi"]):
            print("Skrining Skilas Mobilisasi Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining SKILAS Mobilisasi")
        self.page.locator('[id="rowfrm000032"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "berdiri_di_kursi")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_skilas_malnutrisi(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skilas_malnutrisi"]):
            print("Skrining Skilas Malnutrisi Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining SKILAS Malnutrisi")
        self.page.locator('[id="rowfrm000034"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "berat_badan_berkurang")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "hilang_nafsu_makan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "lila_kurang_21cm")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_skilas_depresi(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skilas_depresi"]):
            print("Skrining Skilas Gejala Depresi Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining SKILAS Gejala Depresi")
        self.page.locator('[id="rowfrm000038"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "2_minggu_terakhir_sedih")).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "2_minggu_sedikit_minat")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gangguan_fungsional(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gangguan_fungsional"]):
            print("Skrining Gangguan Fungsional Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Gangguan Fungsional")
        self.page.locator('[id="rowfrm000040"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "kendali_bab")).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "kendali_bak")).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "membersihkan_diri")).click()
        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "penggunaan_jamban")).click()
        self.page.locator("div[aria-controls='sq_104i_list']").click()
        self.page.locator("#sq_104i_list [role='option']").filter(
            has_text=self.required(data, "makan_minum")).click()
        self.page.locator("div[aria-controls='sq_105i_list']").click()
        self.page.locator("#sq_105i_list [role='option']").filter(
            has_text=self.required(data, "berubah_sikap")).click()
        self.page.locator("div[aria-controls='sq_106i_list']").click()
        self.page.locator("#sq_106i_list [role='option']").filter(
            has_text=self.required(data, "berpindah")).click()
        self.page.locator("div[aria-controls='sq_107i_list']").click()
        self.page.locator("#sq_107i_list [role='option']").filter(
            has_text=self.required(data, "memakai_baju")).click()
        self.page.locator("div[aria-controls='sq_108i_list']").click()
        self.page.locator("#sq_108i_list [role='option']").filter(
            has_text=self.required(data, "naik_turun_tangga")).click()
        self.page.locator("div[aria-controls='sq_109i_list']").click()
        self.page.locator("#sq_109i_list [role='option']").filter(
            has_text=self.required(data, "mandi")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_mini_cog(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_mini_cog"]):
            print("Skrining Mini COG Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Mini COG")
        self.page.locator('[id="rowfrm000030"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "mini_cog_1")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "mini_cog_2")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "mini_cog_3")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_ad8_ina(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_ad8_ina"]):
            print("Skrining AD-8 INA Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining AD-8 INA")
        self.page.locator('[id="rowfrm000031"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "ina_1")).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "ina_2")).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "ina_3")).click()
        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "ina_4")).click()
        self.page.locator("div[aria-controls='sq_104i_list']").click()
        self.page.locator("#sq_104i_list [role='option']").filter(
            has_text=self.required(data, "ina_5")).click()
        self.page.locator("div[aria-controls='sq_105i_list']").click()
        self.page.locator("#sq_105i_list [role='option']").filter(
            has_text=self.required(data, "ina_6")).click()
        self.page.locator("div[aria-controls='sq_106i_list']").click()
        self.page.locator("#sq_106i_list [role='option']").filter(
            has_text=self.required(data, "ina_7")).click()
        self.page.locator("div[aria-controls='sq_107i_list']").click()
        self.page.locator("#sq_107i_list [role='option']").filter(
            has_text=self.required(data, "ina_8")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_mobilisasi_lanjutan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_mobilisasi_lanjutan"]):
            print("Skrining Mobilisasi Lanjutan Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Mobilisasi Lanjutan")
        self.page.locator('[id="rowfrm000033"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "sppb_1")).first.click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "sppb_2")).first.click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "sppb_3")).first.click()
        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "sppb_4")).click()
        self.page.locator("div[aria-controls='sq_104i_list']").click()
        self.page.locator("#sq_104i_list [role='option']").filter(
            has_text=self.required(data, "sppb_5")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_malnutrisi_lanjutan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_malnutrisi_lanjutan"]):
            print("Skrining Malnutrisi Lanjutan Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Malnutrisi Lanjutan")
        self.page.locator('[id="rowfrm000035"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_1")).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_2")).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_3")).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "mna_sf_4")
        ).click()
        self.page.locator("div[aria-controls='sq_104i_list']").click()
        self.page.locator("#sq_104i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_5")).click()
        self.page.locator("div[aria-controls='sq_105i_list']").click()
        self.page.locator("#sq_105i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_6")).click()
        self.page.locator("div[aria-controls='sq_106i_list']").click()
        self.page.locator("#sq_106i_list [role='option']").filter(
            has_text=self.required(data, "mna_sf_7")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_depresi_lanjutan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_depresi_lanjutan"]):
            print("Skrining Depresi Lanjutan Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Depresi Lanjutan")
        self.page.locator('[id="rowfrm000039"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "depresi_lanjutan_1")).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_lanjutan_2")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_lanjutan_3")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_lanjutan_4")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_gula_darah_dewasa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gula_darah_dewasa"]):
            print("Skrining Gizi Laki Dilewati (Tidak Aktif)")
            return

        label = "Pemeriksaan Gula Darah Dewasa Lansia"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Gula Darah Dewasa")
        self.page.locator('[id="rowfrm000256"]').click()
        pernah_diabetes = self.required(data, "pernah_diabetes")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=pernah_diabetes
        ).click()
        if pernah_diabetes == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.required(data, "total_bulan_diabetes")
            )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "gula_darah_sewaktu")
        )
        if pernah_diabetes == "Tidak":
            self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
                self.required(data, "gula_darah_sewaktu_2")
            )
        self.page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
            self.required(data, "gula_darah_puasa")
        )
        self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
            self.required(data, "gula_darah_pp")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_tekanan_darah_dewasa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_tekanan_darah_dewasa"]):
            print("Skrining Gizi Laki Dilewati (Tidak Aktif)")
            return
        
        label = "Tekanan Darah Dewasa Lansia"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
    
        self.page.locator("#rowfrm000265").click()
        self._start_screening("Skrining Tekanan Darah Dewasa")
        # self.page.locator('[id="rowfrm000265"]').click()
        pernah_hipertensi = self.required(data, "pernah_hipertensi")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=pernah_hipertensi
        ).click()
        if pernah_hipertensi == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.required(data, "total_bulan_hipertensi")
            )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "sistolik")
        )
        self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            self.required(data, "diastolik")
        )
        self.page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
            self.required(data, "sistolik_2")
        )
        self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
            self.required(data, "diastolik_2")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_telinga_mata_18_39(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_telinga_mata_18_39"]):
            print("Skrining Telinga dan Mata (18 - 39 tahun) Dilewati (Tidak Aktif)")
            return
        label = "Skrining Telinga dan Mata (18-39 tahun)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Telinga dan Mata (18-39 tahun)")
        self.page.locator('[id="rowfrm000042"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "infeksi_telinga")
        ).click()
        # self.page.locator("div[aria-controls='sq_101i_list']").click()
        # self.page.locator("#sq_101i_list [role='option']").filter(
        #     has_text=self.required(data, "infeksi_telinga")).first.click()
        tajam_pendengaran = self.required(data, "tajam_pendengaran")
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=tajam_pendengaran
        ).first.click()
        if tajam_pendengaran == "Curiga gangguan pendengaran":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "tes_penala")
            ).first.click()
        tajam_penglihatan = self.required(data, "tajam_penglihatan")
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=tajam_penglihatan
        ).first.click()
        if tajam_penglihatan == "Curiga gangguan penglihatan (visus <6/12)":
            hasil_visus = self.required(data, "hasil_visus")
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=hasil_visus
            ).first.click()
            if hasil_visus != "Normal (visus 6/6 - 6/12)":
                pinhole = self.required(data, "pinhole")
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=pinhole
                ).first.click()
                if pinhole == "Visus membaik":
                    self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
                        has_text=self.required(data, "hasil_refraksi")
                    ).first.click()
                else:
                    self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
                        has_text=self.required(data, "funduskopi")
                    ).first.click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_risiko_tb(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb"]):
            print("Skrining Risiko TB Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko dan Skrining X-Ray TB (Dewasa & Lansia)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Risiko TB")
        self.page.locator('[id="rowfrm000182"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_batuk_tidak_sembuh")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "bb_turun")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "demam_hilang_timbul")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "berkeringat_malam")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "pembesaran_getah_bening")
        ).click()
        radiografi_toraks = self.required(data, "radiografi_toraks")
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=radiografi_toraks
        ).click()
        if radiografi_toraks == "Ya":
            value = self.required(data, "hasil_rontgen")
            self.page.locator(
                "fieldset[aria-labelledby='sq_106_ariaTitle'] label"
            ).filter(
                has_text=re.compile(rf"^{re.escape(value)}$")
            ).click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
        # page.pause()

    def do_tb(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_tb"]):
            print("Skrining TB Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Tuberkulosis (Dewasa & Lansia)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining TB")
        self.page.locator('[id="rowfrm000184"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        kontak_tbc = self.required(data, "kontak_tbc")
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=kontak_tbc).click()
        if kontak_tbc == "Riwayat kontak serumah" or kontak_tbc == "Riwayat kontak erat":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_tbc")
            ).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        metode_pemeriksaan_tbc = self.required(data, "metode_pemeriksaan_tbc")
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=metode_pemeriksaan_tbc).click()
        if metode_pemeriksaan_tbc == "TCM":
            # print("TCM")
            self.page.locator("div#sq_103i.sd-input.sd-dropdown").click()
            self.page.locator("#sq_103i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif metode_pemeriksaan_tbc == "BTA":
            self.page.locator("div[aria-controls='sq_104i_list']").click()
            self.page.locator("#sq_104i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif metode_pemeriksaan_tbc == "NPOC":
            self.page.locator("div[aria-controls='sq_105i_list']").click()
            self.page.locator("#sq_105i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_frambusia(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_frambusia"]):
            print("Skrining Frambusia Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Penyakit Frambusia (untuk daerah endemis atau berisiko frambusia)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Frambusia")
        self.page.locator('[id="rowfrm000199"]').click()
        ada_papul = self.required(data, "ada_papul")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=ada_papul
        ).click()
        if ada_papul == "Suspek frambusia":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_pemeriksaan_rdt")
            ).first.click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()




    def do_kusta(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kusta"]):
            print("Skrining Kusta Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Penyakit Kusta"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Kusta")
        self.page.locator('[id="rowfrm000198"]').click()
        bercak_putih = self.required(data, "bercak_putih")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=bercak_putih
        ).first.click()
        # self.page.locator("div[aria-controls='sq_100i_list']").click()
        # self.page.locator("#sq_100i_list [role='option']").filter(has_text=bercak_putih).click()
        if bercak_putih == "Meragukan":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_bta")
            ).first.click()
            # self.page.locator("div[aria-controls='sq_101i_list']").click()
            # self.page.locator("#sq_101i_list [role='option']").filter(
            #     has_text=self.required(data, "hasil_bta")).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_skabies(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skabies"]):
            print("Skrining Skabies Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Penyakit Skabies"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Skabies")
        self.page.locator('[id="rowfrm000201"]').click()
        # self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "ada_ruam")
        ).first.click()
        # self.page.locator("#sq_100i_list [role='option']").filter(has_text=self.required(data, "ada_ruam")).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_telinga_mata(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_telinga_mata"]):
            print("Skrining Telinga dan Mata Dilewati (Tidak Aktif)")
            return
        label = "Skrining Telinga dan Mata (=>40 tahun)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Telinga dan Mata")
        self.page.locator('[id="rowfrm000099"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "infeksi_telinga")
        ).first.click()
        # self.page.locator("div[aria-controls='sq_101i_list']").click()
        # self.page.locator("#sq_101i_list [role='option']").filter(
        #     has_text=self.required(data, "infeksi_telinga")).first.click()
        tajam_pendengaran = self.required(data, "tajam_pendengaran")
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=tajam_pendengaran
        ).first.click()
        if tajam_pendengaran == "Curiga gangguan pendengaran":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "tes_penala")
            ).first.click()
        tajam_penglihatan = self.required(data, "tajam_penglihatan")
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=tajam_penglihatan
        ).first.click()
        if tajam_penglihatan == "Curiga gangguan penglihatan (visus <6/12)":
            hasil_visus = self.required(data, "hasil_visus")
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=hasil_visus
            ).first.click()
            if hasil_visus != "Normal (visus 6/6 - 6/12)":
                pinhole = self.required(data, "pinhole")
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=pinhole
                ).first.click()
                if pinhole == "Visus membaik":
                    self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
                        has_text=self.required(data, "hasil_refraksi")
                    ).first.click()
                else:
                    self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
                        has_text=self.required(data, "funduskopi")
                    ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_109_ariaTitle'] label").filter(
            has_text=self.required(data, "pupil")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_karies(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_karies"]):
            print("Skrining Karies Dilewati (Tidak Aktif)")
            return
        label = "Skrining Karies dan Gigi Hilang"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Karies")
        self.page.locator('[id="rowfrm000055"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_karies")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_hilang")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_periodontal(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_periodontal"]):
            print("Skrining Periodontal Dilewati (Tidak Aktif)")
            return
        label = "Skrining Penyakit Periodontal"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Periodontal")
        self.page.locator('[id="rowfrm000056"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "penyakit_periodontal")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_goyang")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_ppok(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_ppok"]):
            print("Skrining PPOK Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan PPOK (Skrining PUMA)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining PPOK")
        self.page.locator('[id="rowfrm000101"]').click()
        # self.page.pause()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "usia_skor_puma")
        ).first.click()
        ppok_merokok = self.required(data, "ppok_merokok")
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=ppok_merokok
        ).first.click()
        if ppok_merokok == "Iya":
            self.page.locator("div[aria-controls='sq_102i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "bungkus_per_tahun")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "nafas_pendek")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "mempunyai_dahak")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "batuk_tanpa_flu")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "periksa_spirometri")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kadar_co(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kadar_co"]):
            print("Skrining Kadar CO Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Kadar CO (Hanya Diisi Apabila Merokok atau Terpapar Asap Rokok)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Kadar CO")
        self.page.locator('[id="rowfrm000186"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "kadar_co")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_lipid(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_lipid"]):
            print("Skrining Lipid Dilewati (Tidak Aktif)")
            return
        label = "POCT Lipid Panel (Khusus usia >=40 thn dan penyandang HT dan/atau DM)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Lipid")
        self.page.locator('[id="rowfrm000047"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "kolesterol")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "hdl")
        )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "ldl")
        )
        self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            self.required(data, "trigliserida")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_fibrosis(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_fibrosis"]):
            print("Skrining Fibrosis Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Fibrosis/Sirosis Hati"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Fibrosis")
        self.page.locator('[id="rowfrm000045"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "sgot")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "trombosit")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_hepatitis(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hepatitis"]):
            print("Skrining Hepatitis Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Hepatitis"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Hepatitis")
        self.page.locator('[id="rowfrm000044"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_b")
        ).first.click()
        hepatitis_c = self.required(data, "hepatitis_c")
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=hepatitis_c
        ).first.click()
        if hepatitis_c == "Anti HCV Reaktif":
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "vl_hepatitis_c")
            ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_fungsi_ginjal(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_fungsi_ginjal"]):
            print("Skrining Fungsi Ginjal Dilewati (Tidak Aktif)")
            return
        label = "Skrining Fungsi Ginjal Laki-Laki (hanya untuk =>40 tahun dengan risiko HT DM)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Fungsi Ginjal")
        self.page.locator('[id="rowfrm000244"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "kreatinin")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "ureum")
        )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "usia")
        )
        self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            self.required(data, "e_lfg")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_fungsi_ginjal_perempuan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_fungsi_ginjal_perempuan"]):
            print("Skrining Fungsi Ginjal Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Fungsi Ginjal")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-3']", True)
        self.page.locator('[id="rowfrm000245"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "kreatinin")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "ureum")
        )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "usia")
        )
        self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            self.required(data, "e_lfg")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kerusakan_ginjal(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kerusakan_ginjal"]):
            print("Skrining Kerusakan Ginjal Dilewati (Tidak Aktif)")
            return
        label = "Skrining Kerusakan Ginjal (hanya untuk =>40 tahun dengan risiko HT DM)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Kerusakan Ginjal")
        self.page.locator('[id="rowfrm000248"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "albumin")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "kreatinin_urin")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kanker_payudara(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kanker_payudara"]):
            print("Skrining Kanker Payudara Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Kanker Payudara")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000059"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        pemeriksaan_payudara = self.required(data, "pemeriksaan_payudara")
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=pemeriksaan_payudara).first.click()
        if pemeriksaan_payudara == "SADANIS":
            self.page.locator("div[aria-controls='sq_101i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "hasil_sadanis")).first.click()
        else:
            self.page.locator("div[aria-controls='sq_102i_list']").click()
            self.page.locator("#sq_102i_list [role='option']").filter(
                has_text=self.required(data, "hasil_usg_payudara")).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_hpv_dna(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hpv_dna"]):
            print("Skrining HPV DNA Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining HPV DNA")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000061"]').click()
        pemeriksaan_hpv_dna = self.required(data, "pemeriksaan_hpv_dna")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=pemeriksaan_hpv_dna
        ).first.click()
        if pemeriksaan_hpv_dna == "HPV Positif":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hpv_16")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "hpv_18")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "hpv_52")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.required(data, "hpv_enkogenik_lain")
            ).first.click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_inspekulo_iva(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_inspekulo_iva"]):
            print("Skrining Inspekulo IVA Dilewati (Tidak Aktif)")
            return
        self._start_screening("Skrining Inspekulo dan IVA")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000060"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "inspekulo")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "iva")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_jantung(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_jantung"]):
            print("Skrining Jantung Dilewati (Tidak Aktif)")
            return
        label = "Hasil Pemeriksaan - Skrining Jantung"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Jantung")
        self.page.locator('[id="rowfrm000057"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "ekg")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "pemeriksaan_ekg")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kanker_usus(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kanker_usus"]):
            print("Skrining Kanker Usus Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Lanjutan Kanker Usus"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Kanker Usus")
        self.page.locator('[id="rowfrm000050"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "bersedia_colok_dubur")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "colok_dubur")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "darah_samar")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kanker_paru(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kanker_paru"]):
            print("Skrining Kanker Paru Dilewati (Tidak Aktif)")
            return
        label = "Skrining Kanker Paru (Usia =>45 thn)"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return
        self._start_screening("Skrining Kanker Paru")
        self.page.locator('[id="rowfrm000041"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "jenis_kelamin_skor_apcs")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "usia_skor_apcs")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "kanker_paru")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "keluarga_kanker")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "riwayat_merokok")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "tempat_kerja_karsinogenik")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "tempat_tinggal_potensi_tinggi")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "lingkungan_tidak_sehat")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
            has_text=self.required(data, "penyakit_paru_kronik")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_109_ariaTitle'] label").filter(
            has_text=self.required(data, "foto_torax")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_catin_perempuan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_catin_perempuan"]):
            print("Skrining Catin Perempuan Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Calon Pengantin Perempuan"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Catin Perempuan")
        self.page.locator('[id="rowfrm000205"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "hemoglobin")
        )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_hiv(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hiv"]):
            print("Skrining HIV Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan HIV"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining HIV")
        self.page.locator('[id="rowfrm000188"]').click()
        rapid_test = self.required(data, "rapid_test")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=rapid_test
        ).first.click()
        if rapid_test == "Reaktif":
            r2_hiv = self.required(data, "r2_hiv")
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=r2_hiv
            ).first.click()
            if r2_hiv == "Reaktif":
                self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                    has_text=self.required(data, "r3_hiv")
                ).first.click()
            elif r2_hiv == "Non Reaktif":
                self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                    has_text=self.required(data, "r1_hiv_ulang")
                ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_sifilis(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_sifilis"]):
            print("Skrining Sifilis Dilewati (Tidak Aktif)")
            return
        label = "Pemeriksaan Sifilis"
        row = self.page.locator("div.w-full.grid.grid-cols-5").filter(
            has=self.page.get_by_text(label, exact=True)
        )
        already_done = row.get_by_text(
            "Selesai Pemeriksaan", exact=True
        ).count() > 0
        if already_done:
            print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
            return

        self._start_screening("Skrining Sifilis")
        self.page.locator('[id="rowfrm000191"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "rapid_test_sifilis")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
