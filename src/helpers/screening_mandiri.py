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

class ScreeningMandiri:
    _SCREENING_KEYS = {
        "do_demografi_dewasa": "skrining_demografi",
        "do_demografi_dewasa_perempuan": "skrining_demografi",
        "do_demografi_lansia": "skrining_demografi",
        "do_demografi_anak": "skrining_demografi",
        "do_risiko_malaria": "skrining_risiko_malaria",
        "do_cemas_anak": "skrining_cemas_anak",
        "do_gejala_depresi_anak": "skrining_gejala_depresi_anak",
        "do_riwayat_imunisasi_rutin_anak_sekolah": "skrining_imunisasi_rutin_anak_sekolah",
        "do_risiko_hepatitis_sd": "skrining_risiko_hepatitis_sd",
        "do_risiko_tb_anak": "skrining_risiko_tb_anak",
        "do_risiko_gula_darah_anak": "skrining_risiko_gula_darah_anak",
        "do_imunisasi_rutin_balita": "skrining_imunisasi_rutin_balita",
        "do_risiko_kanker_usus": "skrining_kanker_usus_mandiri",
        "do_risiko_tb": "skrining_risiko_tb",
        "do_hati": "skrining_hati",
        "do_leher_rahim": "skrining_kanker_leher_rahim",
        "do_keswa": "skrining_kesehatan_jiwa",
        "do_imunisasi_tetanus": "skrining_imunisasi_tetanus",
        "do_risiko_kanker_paru": "skrining_kanker_paru",
        "do_perilaku_merokok": "skrining_perilaku_merokok",
        "do_aktivitas_fisik": "skrining_aktivitas_fisik",
        "do_keswa_remaja": "skrining_keswa",
        "do_keswa_remaja_2": "skrining_keswa_2",
        "do_aktivitas_fisik_remaja": "skrining_aktivitas_fisik_remaja",
        "do_kelayakan_tes_kebugaran": "skrining_kelayakan_tes_kebugaran",
        "do_kesehatan_reproduksi": "skrining_kesehatan_reproduksi",
        "do_imunisasi_hpv": "skrining_imunisasi_hpv",
        "do_faktor_risiko_hepatitis_remaja": "skrining_faktor_risiko_hepatitis_remaja",
        "do_perilaku_merokok_remaja": "skrining_perilaku_merokok_remaja"

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
        return value

    def _skip_if_screening_done(self, form_id: str, label: str) -> bool:
        row = self.page.locator("tr").filter(
            has=self.page.locator(f"#{form_id}")
        )
        row.wait_for()
        if row.locator('img[src$="/icon-success.svg"]').count() == 0:
            return False
        print(f"{Colors.OKGREEN}{label} sudah selesai; dilewati{Colors.ENDC}")
        return True


    def do_demografi_dewasa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_dewasa"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return
        label = "Demografi Dewasa Laki-Laki"
        if self._skip_if_screening_done("rowfrm000006", label):
            return
        self._start_screening("Skrining Demografi Dewasa")
        self.page.locator('[id="rowfrm000006"]').click()

        value = self.required(data, "status_perkawinan")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).first.click()
        # self.page.get_by_label(self.required(data, "status_perkawinan"), exact=True).click()
        if value != "Menikah":
            self.page.locator("label").filter(
                has_text=self.required(data, "rencana_menikah")
            ).click()

        self.page.locator("label").filter(
            has_text=self.required(data, "disabilitas")
        ).click()

        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_demografi_dewasa_perempuan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_dewasa_perempuan"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return
        
        label = "Demografi Dewasa Perempuan"
        if self._skip_if_screening_done("rowfrm000007", label):
            return

        self._start_screening("Skrining Demografi Dewasa Perempuan")
        self.page.locator('[id="rowfrm000007"]').click()
        value = self.required(data, "status_perkawinan")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).first.click()
        if value != "Menikah":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "rencana_menikah")
            ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "sedang_hamil")
        ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "disabilitas")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_demografi_lansia(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_lansia"]):
            print("Skrining Demografi Lansia Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000008", "Demografi Lansia"):
            return
        
        self._start_screening("Skrining Demografi Lansia")
        self.page.locator('[id="rowfrm000008"]').click()
        value = self.required(data, "status_perkawinan")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "disabilitas")
        ).first.click()

        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_demografi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_anak"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return
        
        if self._skip_if_screening_done("rowfrm000106", "Demografi Anak"):
            return
        self._start_screening("Skrining Demografi Anak")
        self.page.locator('[id="rowfrm000106"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "disabilitas")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_risiko_malaria(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_malaria"]):
            print("Skrining Risiko Malaria Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko Malaria"
        if self._skip_if_screening_done("rowfrm000115", label):
            return
        
        self._start_screening("Skrining Risiko Malaria")
        self.page.locator('[id="rowfrm000115"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "malaria_1")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "malaria_2")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "malaria_3")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "malaria_4")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_cemas_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_cemas_anak"]):
            print("Skrining Cemas Anak Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000109", "Skrining Cemas Anak"):
            return
        
        self._start_screening("Skrining Cemas Anak")
        self.page.locator('[id="rowfrm000109"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "cemas_1")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "cemas_2")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "cemas_3")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_gejala_depresi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gejala_depresi_anak"]):
            print("Skrining Gejala Depresi Anak Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000124", "Skrining Gejala Depresi Anak"):
            return
        self._start_screening("Skrining Gejala Depresi Anak")
        self.page.locator('[id="rowfrm000124"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_1")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_2")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "depresi_3")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_riwayat_imunisasi_rutin_anak_sekolah(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_riwayat_imunisasi_rutin_anak_sekolah"]):
            print("Skrining Riwayat Imunisasi Rutin Anak Sekolah Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000129", "Skrining Riwayat Imunisasi Rutin Anak Sekolah"):
            return
        self._start_screening("Skrining Riwayat Imunisasi Rutin Anak Sekolah")
        self.page.locator('[id="rowfrm000129"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "memperoleh_imunisasi_polio")).click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_risiko_hepatitis_sd(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_hepatitis_sd"]):
            print("Skrining Risiko Hepatitis SD Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000114", "Skrining Risiko Hepatitis SD"):
            return
        self._start_screening("Skrining Risiko Hepatitis SD")
        self.page.locator('[id="rowfrm000114"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_sd_1")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_sd_2")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_sd_3")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_sd_4")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_risiko_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb_anak"]):
            print("Skrining Risiko TB Anak Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000174", "Skrining Risiko TB Anak"):
            return
        self._start_screening("Skrining Risiko TB Anak 1-9 Tahun")
        self.page.locator('[id="rowfrm000174"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "risiko_tb_anak")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_risiko_gula_darah_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_gula_darah_anak"]):
            print("Skrining Risiko Gula Darah Anak Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000110", "Skrining Risiko Gula Darah Anak"):
            return
        self._start_screening("Skrining Risiko Gula Darah Anak")
        self.page.locator('[id="rowfrm000110"]').click()
        pernah_kencing_manis = self.required(data, "pernah_kencing_manis")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=pernah_kencing_manis
        ).first.click()
        if pernah_kencing_manis == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "berapa_bulan_diabetes"))
        else:
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "sering_lapar")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "sering_haus")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.required(data, "penurunan_berat_badan")
            ).first.click()
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "anggota_keluarga_diabetes")
            ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_imunisasi_rutin_balita(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_imunisasi_rutin_balita"]):
            print("Skrining Imunisasi Rutin Balita Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000171", "Skrining Imunisasi Rutin Balita"):
            return
        self._start_screening("Skrining Imunisasi Rutin Balita")
        self.page.locator('[id="rowfrm000171"]').click()

        imunisasi_24_bulan = self.required(data, "imunisasi_24_bulan")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(has_text=imunisasi_24_bulan).first.click()
        if imunisasi_24_bulan == "Ya":
            membawa_buku_imunisasi = self.required(data, "membawa_buku_imunisasi")
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(has_text=membawa_buku_imunisasi).first.click()
            if membawa_buku_imunisasi == "Ya":
                self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_hepatitis_b")).click()
                self.page.locator("div[aria-controls='sq_103i_list']").click()
                self.page.locator('div.sd-dropdown[aria-label^="Apakah anak anda sudah pernah menerima imunisasi BCG"]').click()
                self.page.locator("#sq_103i_list [role='option']").filter(has_text=self.required(data, "menerima_imunisasi_bcg")).click()
                self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv")).click()
                self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt")).click()
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_2")).click()
                self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_pcv")).click()
                self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus")).click()
                self.page.locator("fieldset[aria-labelledby='sq_109_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_2")).click()
                self.page.locator("fieldset[aria-labelledby='sq_110_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_3")).click()
                self.page.locator("fieldset[aria-labelledby='sq_111_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_pcv_2")).click()
                self.page.locator("fieldset[aria-labelledby='sq_112_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus_2")).click()
                self.page.locator("fieldset[aria-labelledby='sq_113_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_3")).click()
                self.page.locator("fieldset[aria-labelledby='sq_114_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_4")).click()
                self.page.locator("fieldset[aria-labelledby='sq_115_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus_3")).click()
                self.page.locator("fieldset[aria-labelledby='sq_116_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_ipv")).click()
                self.page.locator("fieldset[aria-labelledby='sq_117_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_campak")).click()
                self.page.locator("fieldset[aria-labelledby='sq_118_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_4")).click()
                self.page.locator("fieldset[aria-labelledby='sq_119_ariaTitle'] label").filter(
                    has_text=self.required(data, "menerima_imunisasi_campak_2")).click()

        self.page.locator("input:has-text('Kirim')").click()

        self._finish_screening()

    def do_risiko_kanker_usus(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_kanker_usus"]):
            print("Skrining Kanker Usus Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko Kanker Usus"
        if self._skip_if_screening_done("rowfrm000027", label):
            return
        self._start_screening("Skrining Risiko Kanker Usus")
        self.page.locator('[id="rowfrm000027"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "keluarga_kanker_usus")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "merokok")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "usia_skor_apcs_mandiri")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "jenis_kelamin_apcs_mandiri")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_risiko_tb(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb"]):
            print("Skrining Risiko TB Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko TB - Mandiri"
        if self._skip_if_screening_done("rowfrm000180", label):
            return
        self._start_screening("Skrining Risiko TB")
        self.page.locator('[id="rowfrm000180"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "batuk_tidak_sembuh")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_keswa_remaja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_keswa_remaja"]):
            print("Skrining Kesehatan Jiwa Dilewati (Tidak Aktif)")
            return
        label = "Kesehatan Jiwa"
        form_id = "rowfrm000112"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Kesehatan Jiwa")
        self.page.locator(f'[id="{form_id}"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "tidak_tenang")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "berpikir_berlebihan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "sulit_tidur")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_keswa_remaja_2(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_keswa_remaja_2"]):
            print("Skrining Kesehatan Jiwa Dilewati (Tidak Aktif)")
            return
        label = "Kesehatan Jiwa"
        form_id = "rowfrm000125"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Kesehatan Jiwa")
        self.page.locator('[id="rowfrm000125"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "merasa_sedih")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "tidak_tertarik_lagi")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "sulit_fokus")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_aktivitas_fisik_remaja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_aktivitas_fisik_remaja"]):
            print("Skrining Aktivitas Fisik Remaja Dilewati (Tidak Aktif)")
            return
        label = "Aktivitas Fisik Remaja"
        form_id = "rowfrm000121"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Aktivitas Fisik Remaja")
        self.page.locator('[id="rowfrm000121"]').click()
        
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").press_sequentially(self.required(data, "hari_aktivitas_fisik"), delay=100)
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").press_sequentially(self.required(data, "menit_aktivitas_fisik"), delay=100)
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_kelayakan_tes_kebugaran(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kelayakan_tes_kebugaran"]):
            print("Skrining Kelayakan Tes Kebugaran Dilewati (Tidak Aktif)")
            return
        label = "Kelayakan Tes Kebugaran"
        form_id = "rowfrm000113"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Kelayakan Tes Kebugaran")
        self.page.locator('[id="rowfrm000113"]').click()
        			
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "masalah_tulang_dan_sendi")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "masalah_jantung")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "terserang_asma")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_pingsan")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
    
    
    def do_kesehatan_reproduksi(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kesehatan_reproduksi"]):
            print("Skrining Kesehatan Reproduksi Dilewati (Tidak Aktif)")
            return
        label = "Kesehatan Reproduksi"
        form_id = "rowfrm000123"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Kesehatan Reproduksi")
        self.page.locator('[id="rowfrm000123"]').click()
        			
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "sudah_menstruasi")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "menstruasi_pertama")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "keputihan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "gatal_kemaluan")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
        
    def do_imunisasi_hpv(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_imunisasi_hpv"]):
            print("Skrining Imunisasi HPV Dilewati (Tidak Aktif)")
            return
        label = "Imunisasi HPV"
        form_id = "rowfrm000130"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Imunisasi HPV")
        self.page.locator('[id="rowfrm000130"]').click()
        			
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "sudah_hpv")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_faktor_risiko_hepatitis_remaja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_faktor_risiko_hepatitis_remaja"]):
            print("Skrining Faktor Risiko Hepatitis Remaja Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko Hepatitis Remaja"
        form_id = "rowfrm000122"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Faktor Risiko Hepatitis Remaja")
        self.page.locator('[id="rowfrm000122"]').click()
        			
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_positif_hepatitis_b")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "keluarga_hepatitis_b")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_seksual_berisiko")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_menerima_transfusi_darah")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_cuci_darah")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_narkoba")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "odhiv")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_pengobatan_hepatitis_c")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
    
    def do_perilaku_merokok_remaja(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_perilaku_merokok_remaja"]):
            print("Skrining Perilaku Merokok Remaja Dilewati (Tidak Aktif)")
            return
        label = "Perilaku Merokok"
        form_id = "rowfrm000118"

        if self._skip_if_screening_done(form_id, label):
            return
        self._start_screening("Skrining Perilaku Merokok Remaja")
        self.page.locator('[id="rowfrm000118"]').click()
        merokok_setahun_terakhir = self.required(data, "merokok_setahun_terakhir")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=merokok_setahun_terakhir
        ).click()
        if merokok_setahun_terakhir == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_rokok")
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "berapa_tahun")
            ).click()
            self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").press_sequentially(self.required(data, "berapa_batang"), delay=100)
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "terpapar_asap_rokok")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()


    def do_hati(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hati"]):
            print("Skrining Hati Dilewati (Tidak Aktif)")
            return
        label = "Faktor Risiko Hati"
        if self._skip_if_screening_done("rowfrm000028", label):
            return
        self._start_screening("Skrining Hati")
        self.page.locator('[id="rowfrm000028"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hati_hepatitis_b")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "ibu_hepatitis_b")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "seks_bukan_pasangan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "transfusi_darah")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "hemodialisis")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "pengguna_narkoba")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "odhiv")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "hati_hepatitis_c")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
            has_text=self.required(data, "kolesterol_tinggi")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_leher_rahim(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_leher_rahim"]):
            print("Skrining Kanker Leher Rahim Dilewati (Tidak Aktif)")
            return
        if self._skip_if_screening_done("rowfrm000088", "Skrining Kanker Leher Rahim"):
            return
        self._start_screening("Skrining Kanker Leher Rahim")
        self.page.locator('[id="rowfrm000088"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_seks")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_keswa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_keswa"]):
            print("Skrining Kesehatan Jiwa Dilewati (Tidak Aktif)")
            return
        label = "Kesehatan Jiwa Dewasa"
        if self._skip_if_screening_done("rowfrm000067", label):
            return
        self._start_screening("Skrining Kesehatan Jiwa")
        self.page.locator('[id="rowfrm000067"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "tidak_bersemangat")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "merasa_tertekan")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "gugup_cemas")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "khawatir")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_imunisasi_tetanus(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_imunisasi_tetanus"]):
            print("Skrining Imunisasi Tetanus Dilewati (Tidak Aktif)")
            return
        label = "Riwayat Imunisasi Tetanus(Status T)"
        if self._skip_if_screening_done("rowfrm000172", label):
            return
        self._start_screening("Skrining Imunisasi Tetanus (Status T)")
        self.page.locator('[id="rowfrm000172"]').click()
        riwayat_imunisasi_tetanus = self.required(data, "riwayat_imunisasi_tetanus")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=riwayat_imunisasi_tetanus
        ).first.click()

        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_risiko_kanker_paru(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_kanker_paru"]):
            print("Skrining Risiko Kanker Paru Dilewati (Tidak Aktif)")
            return
        label = "Penapisan Risiko Kanker Paru"
        if self._skip_if_screening_done("rowfrm000138", label):
            return
        self._start_screening("Skrining Kanker Paru")
        self.page.locator('[id="rowfrm000138"]').click()
        merokok_setahun_terakhir = self.required(data, "merokok_setahun_terakhir")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=merokok_setahun_terakhir
        ).click()
        if merokok_setahun_terakhir == "Tidak":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "merokok_15_tahun")
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "terpapar_rokok")
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "kanker_paru_keluarga")
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.required(data, "gejala_batuk")
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "tbc")
            ).click()

        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "terpapar_rokok")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "kanker_paru_keluarga")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "gejala_batuk")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "tbc")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_perilaku_merokok(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_perilaku_merokok"]):
            print("Skrining Perilaku Dilewati (Tidak Aktif)")
            return
        label = "Hasil Perilaku Merokok"
        if self._skip_if_screening_done("rowfrm000064", label):
            return
        
        self._start_screening("Skrining Perilaku Merokok")
        self.page.locator('[id="rowfrm000064"]').click()
        merokok_setahun_terakhir_b = self.required(data, "merokok_setahun_terakhir_b")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=merokok_setahun_terakhir_b
        ).click()

        if merokok_setahun_terakhir_b == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_rokok")
            ).click()
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.required(data, "berapa_tahun")
            )
            self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
                self.required(data, "berapa_batang")
            )

        elif merokok_setahun_terakhir_b == "Tidak":
            pernah_merokok = self.required(data, "pernah_merokok")
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=pernah_merokok
            ).click()
            if pernah_merokok == "Ya":
                self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                    self.required(data, "berapa_tahun_sebelumnya")
                )
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=self.required(data, "kapan_berhenti")
                ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "terpapar_sebulan_terakhir")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()

    def do_aktivitas_fisik(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_aktivitas_fisik"]):
            print("Skrining Aktivitas Fisik Dilewati (Tidak Aktif)")
            return
        label = "Tingkat Aktivitas Fisik"
        if self._skip_if_screening_done("rowfrm000169", label):
            return
        
        self._start_screening("Skrining Aktivitas Fisik")
        self.page.locator('[id="rowfrm000169"]').click()

        
        aktivitas_domestik = self.required(data, "aktivitas_domestik")
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=aktivitas_domestik
        ).first.click()
        if aktivitas_domestik == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.required(data, "hari_domestik")
            )
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.required(data, "menit_domestik")
            )

        aktivitas_pekerjaan = self.required(data, "aktivitas_pekerjaan")
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=aktivitas_pekerjaan
        ).first.click()
        if aktivitas_pekerjaan == "Ya":
            self.page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
                self.required(data, "hari_pekerjaan")
            )
            self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                self.required(data, "menit_pekerjaan")
            )

        aktivitas_perjalanan = self.required(data, "aktivitas_perjalanan")
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=aktivitas_perjalanan
        ).first.click()
        if aktivitas_perjalanan == "Ya":
            self.page.locator("input[aria-labelledby='sq_107_ariaTitle']").fill(
                self.required(data, "hari_perjalanan")
            )
            self.page.locator("input[aria-labelledby='sq_108_ariaTitle']").fill(
                self.required(data, "menit_perjalanan")
            )

        aktivitas_olahraga = self.required(data, "aktivitas_olahraga")
        self.page.locator("fieldset[aria-labelledby='sq_109_ariaTitle'] label").filter(
            has_text=aktivitas_olahraga
        ).first.click()
        if aktivitas_olahraga == "Ya":
            self.page.locator("input[aria-labelledby='sq_110_ariaTitle']").fill(
                self.required(data, "hari_olahraga")
            )
            self.page.locator("input[aria-labelledby='sq_111_ariaTitle']").fill(
                self.required(data, "menit_olahraga")
            )

        aktivitas_kerja_berat = self.required(data, "aktivitas_kerja_berat")
        self.page.locator("fieldset[aria-labelledby='sq_112_ariaTitle'] label").filter(
            has_text=aktivitas_kerja_berat
        ).first.click()
        # self.page.locator("div[aria-controls='sq_112i_list']").click()
        # self.page.locator("#sq_112i .sd-dropdown__value").click()
        # self.page.locator("#sq_112i_list [role='option']").filter(
        #     has_text=aktivitas_kerja_berat).click()
        if aktivitas_kerja_berat == "Ya":
            self.page.locator("input[aria-labelledby='sq_113_ariaTitle']").fill(
                self.required(data, "hari_kerja_berat")
            )
            self.page.locator("input[aria-labelledby='sq_114_ariaTitle']").fill(
                self.required(data, "menit_kerja_berat")
            )

        aktivitas_olahraga_berat = self.required(data, "aktivitas_olahraga_berat")
        self.page.locator("fieldset[aria-labelledby='sq_115_ariaTitle'] label").filter(
            has_text=aktivitas_olahraga_berat
        ).first.click()
        if aktivitas_olahraga_berat == "Ya":
            self.page.locator("input[aria-labelledby='sq_116_ariaTitle']").fill(
                self.required(data, "hari_olahraga_berat")
            )
            self.page.locator("input[aria-labelledby='sq_117_ariaTitle']").fill(
                self.required(data, "menit_olahraga_berat")
            )
        self.page.locator("input:has-text('Kirim')").click()
        self._finish_screening()
