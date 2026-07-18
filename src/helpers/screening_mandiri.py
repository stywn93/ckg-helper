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
    }
    

    def __init__(self, page, formatter):
        self.page = page
        self.formatter = formatter

    def _should_run(self, data:dict, key: str) -> bool:
        value = data.get(key)
        if value is None or str(value).strip() == "":
            return False
        return self.formatter(value) == "Ya"

    def required(self, data: dict, key: str) -> str:
        value = data.get(key)
        if value is None or str(value).strip() == "":
            raise ValueError(f"kolom {key} tidak boleh kosong")
        return self.formatter(value)


    def do_demografi_dewasa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_dewasa"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return

        print("Skrining Demografi Dewasa Dimulai")
        self.page.locator('[id="rowfrm000006"]').click()
        # self.page.locator("label").filter(
        #     has_text=self.required(data, "status_perkawinan")
        # ).first.click()
        self.page.get_by_label(self.required(data, "status_perkawinan"), exact=True).click()
        if data["status_perkawinan"] != "Menikah":
            self.page.locator("label").filter(
                has_text=self.required(data, "rencana_menikah")
            ).click()

        self.page.locator("label").filter(
            has_text=self.required(data, "disabilitas")
        ).click()

        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Dewasa Selesai")

    def do_demografi_dewasa_perempuan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_dewasa_perempuan"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return
        print("Skrining Demografi Dewasa Perempuan Dimulai")
        self.page.locator('[id="rowfrm000007"]').click()
        # self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        #     has_text=self.required(data, "status_perkawinan")
        # ).first.click()
        # self.page.get_by_label(self.required(data, "status_perkawinan"), exact=True).click()
        self.page.get_by_text(self.required(data, "status_perkawinan"), exact=True).click()
        if data["status_perkawinan"] != "Menikah":
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

        print("Skrining Demografi Dewasa Perempuan Selesai")

    def do_demografi_lansia(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_lansia"]):
            print("Skrining Demografi Lansia Dilewati (Tidak Aktif)")
            return
        print("Skrining Demografi Lansia Dimulai")
        self.page.locator('[id="rowfrm000008"]').click()
        # self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        #     has_text=self.required(data, "status_perkawinan")
        # ).first.click()
        self.page.get_by_text(self.required(data, "status_perkawinan"), exact=True).click()

        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "disabilitas")
        ).first.click()

        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Lansia Selesai")

    def do_demografi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_demografi_anak"]):
            print("Skrining Demografi Dewasa Dilewati (Tidak Aktif)")
            return
        print("Skrining Demografi Anak Dimulai")
        self.page.locator('[id="rowfrm000106"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "disabilitas")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Anak Selesai")

    def do_risiko_malaria(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_malaria"]):
            print("Skrining Risiko Malaria Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko Malaria Dimulai")
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

        print("Skrining Risiko Malaria Selesai")

    def do_cemas_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_cemas_anak"]):
            print("Skrining Cemas Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Cemas Anak Dimulai")
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

        print("Skrining Cemas Anak Selesai")

    def do_gejala_depresi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gejala_depresi_anak"]):
            print("Skrining Gejala Depresi Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Gejala Depresi Anak Dimulai")
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

        print("Skrining Gejala Depresi Anak Selesai")

    def do_riwayat_imunisasi_rutin_anak_sekolah(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_riwayat_imunisasi_rutin_anak_sekolah"]):
            print("Skrining Riwayat Imunisasi Rutin Anak Sekolah Dilewati (Tidak Aktif)")
            return
        print("Skrining Riwayat Imunisasi Rutin Anak Sekolah Dimulai")
        self.page.locator('[id="rowfrm000129"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "memperoleh_imunisasi_polio")).click()
        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Riwayat Imunisasi Rutin Anak Sekolah Selesai")

    def do_risiko_hepatitis_sd(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_hepatitis_sd"]):
            print("Skrining Risiko Hepatitis SD Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko Hepatitis SD Dimulai")
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

        print("Skrining Risiko Hepatitis SD Selesai")

    def do_risiko_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb_anak"]):
            print("Skrining Risiko TB Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko TB Anak 1-9 Tahun Dimulai")
        self.page.locator('[id="rowfrm000174"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "risiko_tb_anak")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Risiko TB Anak 1-9 Tahun Selesai")

    def do_risiko_gula_darah_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_gula_darah_anak"]):
            print("Skrining Risiko Gula Darah Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko Gula Darah Anak Dimulai")
        self.page.locator('[id="rowfrm000110"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_kencing_manis")
        ).first.click()
        if self.formatter(data["pernah_kencing_manis"]) == "Ya":
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

        print("Skrining Risiko Gula Darah Anak Selesai")

    def do_imunisasi_rutin_balita(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_imunisasi_rutin_balita"]):
            print("Skrining Imunisasi Rutin Balita Dilewati (Tidak Aktif)")
            return
        print("Skrining Imunisasi Rutin Balita Dimulai")
        self.page.locator('[id="rowfrm000171"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "imunisasi_24_bulan")).click()
        if self.formatter(data["imunisasi_24_bulan"]) == "Ya":
            self.page.locator("div[aria-controls='sq_101i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "membawa_buku_imunisasi")).click()
            if self.formatter(data["membawa_buku_imunisasi"]) == "Ya":
                self.page.locator("div[aria-controls='sq_102i_list']").click()
                self.page.locator("#sq_102i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_hepatitis_b")).click()
                self.page.locator("div[aria-controls='sq_103i_list']").click()
                self.page.locator("#sq_103i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_bcg")).click()
                self.page.locator("div[aria-controls='sq_104i_list']").click()
                self.page.locator("#sq_104i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv")).click()
                self.page.locator("div[aria-controls='sq_105i_list']").click()
                self.page.locator("#sq_105i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt")).click()
                self.page.locator("div[aria-controls='sq_106i_list']").click()
                self.page.locator("#sq_106i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_2")).click()
                self.page.locator("div[aria-controls='sq_107i_list']").click()
                self.page.locator("#sq_107i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_pcv")).click()
                self.page.locator("div[aria-controls='sq_108i_list']").click()
                self.page.locator("#sq_108i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus")).click()
                self.page.locator("div[aria-controls='sq_109i_list']").click()
                self.page.locator("#sq_109i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_2")).click()
                self.page.locator("div[aria-controls='sq_110i_list']").click()
                self.page.locator("#sq_110i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_3")).click()
                self.page.locator("div[aria-controls='sq_111i_list']").click()
                self.page.locator("#sq_111i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_pcv_2")).click()
                self.page.locator("div[aria-controls='sq_112i_list']").click()
                self.page.locator("#sq_112i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus_2")).click()
                self.page.locator("div[aria-controls='sq_113i_list']").click()
                self.page.locator("#sq_113i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_3")).click()
                self.page.locator("div[aria-controls='sq_114i_list']").click()
                self.page.locator("#sq_114i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_opv_4")).click()
                self.page.locator("div[aria-controls='sq_115i_list']").click()
                self.page.locator("#sq_115i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_rotavirus_3")).click()
                self.page.locator("div[aria-controls='sq_116i_list']").click()
                self.page.locator("#sq_116i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_ipv")).click()
                self.page.locator("div[aria-controls='sq_117i_list']").click()
                self.page.locator("#sq_117i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_campak")).click()
                self.page.locator("div[aria-controls='sq_118i_list']").click()
                self.page.locator("#sq_118i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_dpt_4")).click()
                self.page.locator("div[aria-controls='sq_119i_list']").click()
                self.page.locator("#sq_119i_list [role='option']").filter(
                    has_text=self.required(data, "menerima_imunisasi_campak_2")).click()

        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Imunisasi Rutin Balita Selesai")

    def do_risiko_kanker_usus(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_kanker_usus"]):
            print("Skrining Kanker Usus Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko Kanker Usus Dimulai")
        self.page.locator('[id="rowfrm000027"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "keluarga_kanker_usus")
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "merokok")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko Kanker Usus Selesai")

    def do_risiko_tb(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb"]):
            print("Skrining Risiko TB Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko TB Dimulai")
        self.page.locator('[id="rowfrm000180"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "batuk_tidak_sembuh")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko Kanker Usus Selesai")

    def do_hati(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_hati"]):
            print("Skrining Hati Dilewati (Tidak Aktif)")
            return
        print("Skrining Hati Dimulai")
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
        print("Skrining Hati Selesai")

    def do_leher_rahim(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_leher_rahim"]):
            print("Skrining Kanker Leher Rahim Dilewati (Tidak Aktif)")
            return
        print("Skrining Kanker Leher Rahim Dimulai")
        self.page.locator('[id="rowfrm000088"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_seks")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kanker Leher Rahim Selesai")

    def do_keswa(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_keswa"]):
            print("Skrining Kesehatan Jiwa Dilewati (Tidak Aktif)")
            return
        print("Skrining Kesehatan Jiwa Dimulai")
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
        print("Skrining Kesehatan Jiwa Selesai")

    def do_imunisasi_tetanus(self, data: dict, row_number: int) -> None:
        print("Skrining Imunisasi Tetanus (Status T) Dimulai")
        self.page.locator('[id="rowfrm000172"]').click()
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
        print("Skrining Imunisasi Tetanus (Status T) Selesai")

    def do_risiko_kanker_paru(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_kanker_paru"]):
            print("Skrining Risiko Kanker Paru Dilewati (Tidak Aktif)")
            return
        print("Skrining Kanker Paru Dimulai")
        self.page.locator('[id="rowfrm000138"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "merokok_setahun_terakhir")
        ).click()
        if data["merokok_setahun_terakhir"] == "Tidak":
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
        print("Skrining Kanker Paru Selesai")

    def do_perilaku_merokok(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_perilaku_merokok"]):
            print("Skrining Perilaku Dilewati (Tidak Aktif)")
            return
        print("Skrining Perilaku Merokok Dimulai")
        self.page.locator('[id="rowfrm000064"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "merokok_setahun_terakhir_b")
        ).click()

        if data["merokok_setahun_terakhir_b"] == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_rokok")
            ).click()
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.required(data, "berapa_tahun")
            )
            self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
                self.required(data, "berapa_batang")
            )

        elif data["merokok_setahun_terakhir_b"] == "Tidak":
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.required(data, "pernah_merokok")
            ).click()
            if data["pernah_merokok"] == "Ya":
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
        print("Skrining Perilaku Merokok Selesai")

    def do_aktivitas_fisik(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_aktivitas_fisik"]):
            print("Skrining Aktivitas Fisik Dilewati (Tidak Aktif)")
            return
        print("Skrining Aktivitas Fisik Dimulai")
        self.page.locator('[id="rowfrm000169"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_domestik")).click()
        if data["aktivitas_domestik"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.required(data, "hari_domestik")
            )
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.required(data, "menit_domestik")
            )

        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i .sd-dropdown__value").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_pekerjaan")).click()
        if data["aktivitas_pekerjaan"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
                self.required(data, "hari_pekerjaan")
            )
            self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                self.required(data, "menit_pekerjaan")
            )

        self.page.locator("div[aria-controls='sq_106i_list']").click()
        self.page.locator("#sq_106i .sd-dropdown__value").click()
        self.page.locator("#sq_106i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_perjalanan")).click()
        if data["aktivitas_perjalanan"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_107_ariaTitle']").fill(
                self.required(data, "hari_perjalanan")
            )
            self.page.locator("input[aria-labelledby='sq_108_ariaTitle']").fill(
                self.required(data, "menit_perjalanan")
            )

        self.page.locator("div[aria-controls='sq_109i_list']").click()
        self.page.locator("#sq_109i .sd-dropdown__value").click()
        self.page.locator("#sq_109i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_olahraga")).click()
        if data["aktivitas_olahraga"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_110_ariaTitle']").fill(
                self.required(data, "hari_olahraga")
            )
            self.page.locator("input[aria-labelledby='sq_111_ariaTitle']").fill(
                self.required(data, "menit_olahraga")
            )

        self.page.locator("div[aria-controls='sq_112i_list']").click()
        self.page.locator("#sq_112i .sd-dropdown__value").click()

        self.page.locator("#sq_112i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_kerja_berat")).click()
        if data["aktivitas_kerja_berat"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_113_ariaTitle']").fill(
                self.required(data, "hari_kerja_berat")
            )
            self.page.locator("input[aria-labelledby='sq_114_ariaTitle']").fill(
                self.required(data, "menit_kerja_berat")
            )

        self.page.locator("div[aria-controls='sq_115i_list']").click()
        self.page.locator("#sq_115i .sd-dropdown__value").click()
        self.page.locator("#sq_115i_list [role='option']").filter(
            has_text=self.required(data, "aktivitas_olahraga_berat")).click()
        if data["aktivitas_olahraga_berat"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_116_ariaTitle']").fill(
                self.required(data, "hari_olahraga_berat")
            )
            self.page.locator("input[aria-labelledby='sq_117_ariaTitle']").fill(
                self.required(data, "menit_olahraga_berat")
            )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Aktivitas Fisik Selesai")
