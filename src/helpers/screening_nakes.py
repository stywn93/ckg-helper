import re
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
        "do_gizi_laki": "skrining_gizi_laki",
        "do_gizi_perempuan": "skrining_gizi_perempuan",
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
        "do_telinga_mata_18_39": "skrining_telinga_mata_18_39",
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
        "do_fungsi_ginjal_perempuan": "skrining_fungsi_ginjal_perempuan",
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

    def do_pertumbuhan_balita(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_pertumbuhan_balita"]):
            print("Skrining Pertumbuhan Balita Dilewati (Tidak Aktif)")
            return
        print("Skrining Pertumbuhan Balita dan Anak Pra Sekolah dimulai")
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
        print("Skrining Pertumbuhan Balita dan Anak Pra Sekolah selesai")

    def do_kpsp(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kpsp"]):
            print("Skrining KPSP Dilewati (Tidak Aktif)")
            return
        print("Skrining KPSP dimulai")
        self.page.locator('[id="rowfrm000017"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "hasil_kpsp")).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining KPSP selesai")

    def do_m_chat_1(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_m_chat_1"]):
            print("Skrining M Chat 1 Dilewati (Tidak Aktif)")
            return
        print("Skrining M CHAT 1 dimulai")
        self.page.locator('[id="rowfrm000095"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "m_chat_1")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining M CHAT 1 selesai")

    def do_m_chat_2(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_m_chat_2"]):
            print("Skrining M Chat 2 Dilewati (Tidak Aktif)")
            return
        print("Skrining M CHAT 2 dimulai")
        self.page.locator('[id="rowfrm000019"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "m_chat_2"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining M CHAT 2 selesai")

    def do_risiko_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_risiko_tb_anak"]):
            print("Skrining Risiko TB Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Risiko TB dimulai")
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
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "radiografi_toraks")
        ).click()
        if (data["radiografi_toraks"] == "Ya"):
            value = self.required(data, "hasil_rontgen")
            self.page.locator(
                "fieldset[aria-labelledby='sq_106_ariaTitle'] label"
            ).filter(
                has_text=re.compile(rf"^{re.escape(value)}$")
            ).click()

        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko TB selesai")

    def do_tb_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_tb_anak"]):
            print("Skrining TB Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining TB Anak dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-1-1']", True)
        self.page.locator('[id="rowfrm000178"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=self.required(data, "kontak_tbc")).click()
        if data["kontak_tbc"] == "Riwayat kontak serumah" or data["kontak_tbc"] == "Riwayat kontak erat":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_tbc")
            ).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "metode_pemeriksaan_tbc")).click()
        if data["metode_pemeriksaan_tbc"] == "TCM":
            # print("TCM")
            self.page.locator("div#sq_103i.sd-input.sd-dropdown").click()
            self.page.locator("#sq_103i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif data["metode_pemeriksaan_tbc"] == "BTA":
            self.page.locator("div[aria-controls='sq_104i_list']").click()
            self.page.locator("#sq_104i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif data["metode_pemeriksaan_tbc"] == "NPOC":
            self.page.locator("div[aria-controls='sq_105i_list']").click()
            self.page.locator("#sq_105i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining TB Anak selesai")

    def do_riwayat_imunisasi_hepatitis_b(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_riwayat_imunisasi_hepatitis_b"]):
            print("Skrining Riwayat Imunisasi Hepatitis B Dilewati (Tidak Aktif)")
            return
        print("Skrining Riwayat Hepatitis B dimulai")
        self.page.locator('[id="rowfrm000260"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "mendapat_imunisasi_hepatitis_b")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Riwayat Hepatitis B selesai")

    def do_berat_lahir(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do__berat_lahir"]):
            print("Skrining Berat Lahir Dilewati (Tidak Aktif)")
            return
        print("Skrining Berat Lahir dimulai")
        self.page.locator('[id="rowfrm000010"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_lahir"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "berat_sekarang"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Berat Lahir selesai")

    def do_jantung_bawaan(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_jantung_bawaan"]):
            print("Skrining Jantung Bawaan Dilewati (Tidak Aktif)")
            return
        print("Skrining Jantung Bawaan dimulai")
        self.page.locator('[id="rowfrm000011"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "pjb_tangan_kanan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "pjb_kaki"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Jantung Bawaan selesai")

    def do_shk(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_shk"]):
            print("Skrining SHK Dilewati (Tidak Aktif)")
            return
        print("Skrining SHK dimulai")
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
        print("Skrining SHK selesai")

    def do_gizi_anak_sekolah(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_gizi_anak_sekolah"]):
            print("Skrining Gizi Anak Sekolah Dilewati (Tidak Aktif)")
            return
        print("Skrining Gizi Anak Sekolah dimulai")
        self.page.locator('[id="rowfrm000119"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Gizi Anak Sekolah selesai")

    def do_tekanan_darah_anak_remaja(self, data: dict, row_number: int) -> None:
        print("Skrining Tekanan Darah Anak dan Remaja dimulai")
        self.page.locator('[id="rowfrm000266"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "sistol"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "diastol"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Tekanan Darah Anak dan Remaja selesai")

    def do_gula_darah_anak(self, data: dict, row_number: int) -> None:
        print("Skrining Gula Darah Anak dimulai")
        self.page.locator('[id="rowfrm000195"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "anak_pernah_diabetes")
        ).click()
        if self.formatter(data["anak_pernah_diabetes"]) == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "berapa_bulan_diabetes"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "gds"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Gula Darah Anak selesai")

    def do_telinga_mata_anak_sekolah(self, data: dict, row_number: int) -> None:
        print("Skrining Telinga Mata Anak Sekolah dimulai")
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
        print("Skrining Telinga Mata Anak Sekolah selesai")

    def do_hepatitis_b_7_12(self, data: dict, row_number: int) -> None:
        print("Skrining Hepatitis B Usia 7-12 Tahun dimulai")
        self.page.locator('[id="rowfrm000159"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hasil_hepatitis_b")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Hepatitis B Usia 7-12 Tahun selesai")

    def do_rdt_malaria(self, data: dict, row_number: int) -> None:
        print("Skrining RDT Malaria dimulai")
        self.page.locator('[id="rowfrm000117"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hasil_rdt_malaria")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining RDT Malaria selesai")

    def do_darah_tumit(self, data: dict, row_number: int) -> None:
        print("Skrining Darah Tumit dimulai")
        self.page.locator('[id="rowfrm000082"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "darah_tumit")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Darah Tumit selesai")

    def do_konfirmasi_shk(self, data: dict, row_number: int) -> None:
        print("Skrining Konfirmasi SHK dimulai")
        self.page.locator('[id="rowfrm000083"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "dilakukan_konfirmasi_shk")
        ).click()
        if self.formatter(data["dilakukan_konfirmasi_shk"]) == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_shk")
            ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "dilakukan_konfirmasi_g6pd")
        ).click()
        if self.formatter(data["dilakukan_konfirmasi_g6pd"]) == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_g6pd")
            ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "dilakukan_konfirmasi_hak")
        ).click()
        if self.formatter(data["dilakukan_konfirmasi_hak"]) == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_konfirm_hak")
            ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Konfirmasi SHK selesai")

    def do_warna_kulit_dan_tinja(self, data: dict, row_number: int) -> None:
        print("Skrining Edukasi Warna Kulit dan Tinja Bayi dimulai")
        self.page.locator('[id="rowfrm000079"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "dilakukan_edukasi_warna_kulit_dan_tinja")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Edukasi Warna Kulit dan Tinja Bayi selesai")

    def do_hasil_kramer(self, data: dict, row_number: int) -> None:
        print("Skrining Hasil Kramer pada Bayi Kuning dimulai")
        self.page.locator('[id="rowfrm000240"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "nilai_hasil_kramer")).first.click()
        
        # self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        #     has_text=self.required(data, "nilai_hasil_kramer")
        # ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Hasil Kramer pada Bayi Kuning selesai")

    def do_warna_kulit_dan_tinja_28(self, data: dict, row_number: int) -> None:
        print("Skrining Penilaian Warna Kulit dan Tinja 14 - 28 hari dimulai")
        self.page.locator('[id="rowfrm000252"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "tgl_pemeriksaan_kramer"))

        self.page.locator("div#sq_101i.sd-input.sd-dropdown").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "kramer_bayi_kuning")).click()

        self.page.locator("div#sq_102i.sd-input.sd-dropdown").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "derajat_warna_tinja")).click()

        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Penilaian Warna Kulit dan Tinja 14 - 28 hari selesai")

    def do_telinga_mata_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_telinga_mata_anak"]):
            print("Skrining Telinga dan Mata Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Telinga dan Mata Anak dimulai")
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
        print("Skrining Telinga dan Mata Anak selesai")

    def do_periksa_gigi_anak(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_periksa_gigi_anak"]):
            print("Skrining Pemeriksaan Gigi Anak Dilewati (Tidak Aktif)")
            return
        print("Skrining Pemeriksaan Gigi Anak dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-3-0']", True)
        self.page.locator('[id="rowfrm000131"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "jumlah_gigi_karies")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Pemeriksaan Gigi Anak selesai")

    def do_gizi_laki(self, data: dict, row_number: int) -> None:
        print("Skrining Gizi Laki dimulai")
        self.page.locator('[id="rowfrm000093"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "lingkar_perut"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Gizi Laki selesai")

    def do_gizi_perempuan(self, data: dict, row_number: int) -> None:
        print("Skrining Gizi Perempuan dimulai")
        self.page.locator('[id="rowfrm000051"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(self.required(data, "berat_badan"))
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(self.required(data, "tinggi_badan"))
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(self.required(data, "lingkar_perut"))
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Gizi Perempuan selesai")

    def do_skilas_penurunan_kognitif(self, data: dict, row_number: int) -> None:
        print("Skrining SKILAS Penurunan Kognitif dimulai")
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
        print("Skrining SKILAS Penurunan Kognitif selesai")

    def do_skilas_mobilisasi(self, data: dict, row_number: int) -> None:
        print("Skrining SKILAS Mobilisasi dimulai")
        self.page.locator('[id="rowfrm000032"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "berdiri_di_kursi")
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining SKILAS Mobilisasi selesai")

    def do_skilas_malnutrisi(self, data: dict, row_number: int) -> None:
        print("Skrining SKILAS Malnutrisi dimulai")
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
        print("Skrining SKILAS Malnutrisi selesai")

    def do_skilas_depresi(self, data: dict, row_number: int) -> None:
        print("Skrining SKILAS Gejala Depresi dimulai")
        self.page.locator('[id="rowfrm000038"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "2_minggu_terakhir_sedih")).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "2_minggu_sedikit_minat")).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining SKILAS Gejala Depresi selesai")

    def do_gangguan_fungsional(self, data: dict, row_number: int) -> None:
        print("Skrining Gangguan Fungsional dimulai")
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
        print("Skrining Gangguan Fungsional selesai")

    def do_mini_cog(self, data: dict, row_number: int) -> None:
        print("Skrining Mini COG dimulai")
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
        print("Skrining Mini COG selesai")

    def do_ad8_ina(self, data: dict, row_number: int) -> None:
        print("Skrining AD-8 INA dimulai")
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
        print("Skrining AD-8 INA selesai")

    def do_mobilisasi_lanjutan(self, data: dict, row_number: int) -> None:
        print("Skrining Mobilisasi Lanjutan dimulai")
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
        print("Skrining Mobilisasi Lanjutan selesai")

    def do_malnutrisi_lanjutan(self, data: dict, row_number: int) -> None:
        print("Skrining Malnutrisi Lanjutan dimulai")
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
        print("Skrining Malnutrisi Lanjutan selesai")

    def do_depresi_lanjutan(self, data: dict, row_number: int) -> None:
        print("Skrining Depresi Lanjutan dimulai")
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
        print("Skrining Depresi Lanjutan selesai")

    def do_gula_darah_dewasa(self, data: dict, row_number: int) -> None:
        print("Skrining Gula Darah Dewasa dimulai")
        # do_pemeriksaan_check(page, "input#hasil-lab-0-1", True)
        self.page.locator('[id="rowfrm000256"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_diabetes")
        ).click()
        if (data["pernah_diabetes"] == "Ya"):
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.required(data, "total_bulan_diabetes")
            )
        self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            self.required(data, "gula_darah_sewaktu")
        )
        if (data["pernah_diabetes"] == "Tidak"):
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
        print("Skrining Gula Darah Dewasa selesai")

    def do_tekanan_darah_dewasa(self, data: dict, row_number: int) -> None:
        print("Skrining Tekanan Darah Dewasa dimulai")
        # do_pemeriksaan_check(page, "input#hasil-lab-0-2", True)
        self.page.locator('[id="rowfrm000265"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pernah_hipertensi")
        ).click()
        if (data["pernah_hipertensi"] == "Ya"):
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
        print("Skrining Tekanan Darah Dewasa selesai")

    def do_telinga_mata_18_39(self, data: dict, row_number: int) -> None:
        print("Skrining Telinga dan Mata (18-39 tahun) dimulai")
        # do_pemeriksaan_check(page, "input#hasil-lab-0-2", True)
        self.page.locator('[id="rowfrm000042"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi")
        ).click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "infeksi_telinga")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_pendengaran")
        ).first.click()
        if data["tajam_pendengaran"] == "Curiga gangguan pendengaran":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "tes_penala")
            ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_penglihatan")
        ).first.click()
        if data["tajam_penglihatan"] == "Curiga gangguan penglihatan (visus <6/12)":
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_visus")
            ).first.click()
            if data["hasil_visus"] != "Normal (visus 6/6 - 6/12)":
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=self.required(data, "pinhole")
                ).first.click()
                if data["pinhole"] == "Visus membaik":
                    self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
                        has_text=self.required(data, "hasil_refraksi")
                    ).first.click()
                else:
                    self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
                        has_text=self.required(data, "funduskopi")
                    ).first.click()

        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Telinga dan Mata (18-39 tahun) selesai")

    def do_risiko_tb(self, data: dict, row_number: int) -> None:
        print("Skrining Risiko TB dimulai")
        # do_pemeriksaan_check(page, "input#hasil-lab-1-0", True)
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
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "radiografi_toraks")
        ).click()
        if (data["radiografi_toraks"] == "Ya"):
            value = self.required(data, "hasil_rontgen")
            self.page.locator(
                "fieldset[aria-labelledby='sq_106_ariaTitle'] label"
            ).filter(
                has_text=re.compile(rf"^{re.escape(value)}$")
            ).click()

        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko TB selesai")
        # page.pause()

    def do_tb(self, data: dict, row_number: int) -> None:
        print("Skrining TB dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-1-1']", True)
        self.page.locator('[id="rowfrm000184"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=self.required(data, "kontak_tbc")).click()
        if data["kontak_tbc"] == "Riwayat kontak serumah" or data["kontak_tbc"] == "Riwayat kontak erat":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "jenis_tbc")
            ).click()
        self.page.locator("div[aria-controls='sq_102i_list']").click()
        self.page.locator("#sq_102i_list [role='option']").filter(
            has_text=self.required(data, "metode_pemeriksaan_tbc")).click()
        if data["metode_pemeriksaan_tbc"] == "TCM":
            # print("TCM")
            self.page.locator("div#sq_103i.sd-input.sd-dropdown").click()
            self.page.locator("#sq_103i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif data["metode_pemeriksaan_tbc"] == "BTA":
            self.page.locator("div[aria-controls='sq_104i_list']").click()
            self.page.locator("#sq_104i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        elif data["metode_pemeriksaan_tbc"] == "NPOC":
            self.page.locator("div[aria-controls='sq_105i_list']").click()
            self.page.locator("#sq_105i_list [role='option']").filter(
                has_text=self.required(data, "hasil_pemeriksaan_tbc")).click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining TB selesai")

    def do_frambusia(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_frambusia"]):
            print("Skrining Frambusia Dilewati (Tidak Aktif)")
            return
        print("Skrining Frambusia dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-2-0']", True)
        self.page.locator('[id="rowfrm000199"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "ada_papul")
        ).click()
        if data["ada_papul"] == "Suspek frambusia":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_pemeriksaan_rdt")
            ).first.click()
        # page.pause()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Frambusia selesai")

    def do_kusta(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_kusta"]):
            print("Skrining Kusta Dilewati (Tidak Aktif)")
            return
        print("Skrining Kusta dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-2-1']", True)
        self.page.locator('[id="rowfrm000198"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=self.required(data, "bercak_putih")).click()
        if data["bercak_putih"] == "Meragukan":
            self.page.locator("div[aria-controls='sq_101i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "hasil_bta")).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kusta selesai")

    def do_skabies(self, data: dict, row_number: int) -> None:
        if not self._should_run(data, self._SCREENING_KEYS["do_skabies"]):
            print("Skrining Skabies Dilewati (Tidak Aktif)")
            return
        print("Skrining Skabies dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-2-2']", True)
        self.page.locator('[id="rowfrm000201"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(has_text=self.required(data, "ada_ruam")).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Skabies selesai")

    def do_telinga_mata(self, data: dict, row_number: int) -> None:
        print("Skrining Telinga dan Mata dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-3-0']", True)
        self.page.locator('[id="rowfrm000099"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "serumen_impaksi")
        ).first.click()
        self.page.locator("div[aria-controls='sq_101i_list']").click()
        self.page.locator("#sq_101i_list [role='option']").filter(
            has_text=self.required(data, "infeksi_telinga")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_pendengaran")
        ).first.click()
        if data["tajam_pendengaran"] == "Curiga gangguan pendengaran":
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.required(data, "tes_penala")
            ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "tajam_penglihatan")
        ).first.click()
        if data["tajam_penglihatan"] == "Curiga gangguan penglihatan (visus <6/12)":
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.required(data, "hasil_visus")
            ).first.click()
            if data["hasil_visus"] != "Normal (visus 6/6 - 6/12)":
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=self.required(data, "pinhole")
                ).first.click()
                if data["pinhole"] == "Visus membaik":
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
        print("Skrining Telinga dan Mata selesai")

    def do_karies(self, data: dict, row_number: int) -> None:
        print("Skrining Karies dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-4-0']", True)
        self.page.locator('[id="rowfrm000055"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_karies")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_hilang")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Karies selesai")

    def do_periodontal(self, data: dict, row_number: int) -> None:
        print("Skrining Periodontal dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-4-1']", True)
        self.page.locator('[id="rowfrm000056"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "penyakit_periodontal")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "gigi_goyang")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Periodontal selesai")

    def do_ppok(self, data: dict, row_number: int) -> None:
        print("Skrining PPOK dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-5-0']", True)
        self.page.locator('[id="rowfrm000101"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "ppok_merokok")
        ).first.click()
        if data["ppok_merokok"] == "Iya":
            self.page.locator("div[aria-controls='sq_101i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "bungkus_per_tahun")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "nafas_pendek")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "mempunyai_dahak")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "batuk_tanpa_flu")).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "periksa_spirometri")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining PPOK selesai")

    def do_kadar_co(self, data: dict, row_number: int) -> None:
        print("Skrining Kadar CO dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-6-0']", True)
        self.page.locator('[id="rowfrm000186"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "kadar_co")
        )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kadar CO selesai")

    def do_lipid(self, data: dict, row_number: int) -> None:
        print("Skrining Lipid dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-0']", True)
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
        print("Skrining Lipid selesai")

    def do_fibrosis(self, data: dict, row_number: int) -> None:
        print("Skrining Fibrosis dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-1']", True)
        self.page.locator('[id="rowfrm000045"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "sgot")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "trombosit")
        )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Fibrosis selesai")

    def do_hepatitis(self, data: dict, row_number: int) -> None:
        print("Skrining Hepatitis dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-2']", True)
        self.page.locator('[id="rowfrm000044"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_b")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "hepatitis_c")
        ).first.click()
        if data["hepatitis_c"] == "Anti HCV Reaktif":
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.required(data, "vl_hepatitis_c")
            ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Hepatitis selesai")

    def do_fungsi_ginjal(self, data: dict, row_number: int) -> None:
        print("Skrining Fungsi Ginjal dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-3']", True)
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
        print("Skrining Fungsi Ginjal selesai")

    def do_fungsi_ginjal_perempuan(self, data: dict, row_number: int) -> None:
        print("Skrining Fungsi Ginjal dimulai")
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
        print("Skrining Fungsi Ginjal selesai")

    def do_kerusakan_ginjal(self, data: dict, row_number: int) -> None:
        print("Skrining Kerusakan Ginjal dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-7-4']", True)
        self.page.locator('[id="rowfrm000248"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "albumin")
        )
        self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            self.required(data, "kreatinin_urin")
        )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kerusakan Ginjal selesai")

    def do_kanker_payudara(self, data: dict, row_number: int) -> None:
        print("Skrining Kanker Payudara dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000059"]').click()
        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.required(data, "pemeriksaan_payudara")).first.click()
        if data["pemeriksaan_payudara"] == "SADANIS":
            self.page.locator("div[aria-controls='sq_101i_list']").click()
            self.page.locator("#sq_101i_list [role='option']").filter(
                has_text=self.required(data, "hasil_sadanis")).first.click()
        else:
            self.page.locator("div[aria-controls='sq_102i_list']").click()
            self.page.locator("#sq_102i_list [role='option']").filter(
                has_text=self.required(data, "hasil_usg_payudara")).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kanker Payudara selesai")

    def do_hpv_dna(self, data: dict, row_number: int) -> None:
        print("Skrining HPV DNA dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000061"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "pemeriksaan_hpv_dna")
        ).first.click()
        if data["pemeriksaan_hpv_dna"] == "HPV Positif":
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
        print("Skrining HPV DNA selesai")

    def do_inspekulo_iva(self, data: dict, row_number: int) -> None:
        print("Skrining Inspekulo dan IVA dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']", True)
        self.page.locator('[id="rowfrm000060"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "inspekulo")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "iva")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Inspekulo dan IVA selesai")

    def do_jantung(self, data: dict, row_number: int) -> None:
        print("Skrining Jantung dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-8-0']",True)  # butuh penyesuaian berdasarkan siklus hidupnya atau bisa juga tahapan ini dilewati dengan asumsi saat pertama kali dibuka semuanya akan Ya
        self.page.locator('[id="rowfrm000057"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "ekg")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "pemeriksaan_ekg")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Jantung selesai")

    def do_kanker_usus(self, data: dict, row_number: int) -> None:
        print("Skrining Kanker Usus dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-9-0']", True)
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
        print("Skrining Kanker Usus selesai")

    def do_kanker_paru(self, data: dict, row_number: int) -> None:
        print("Skrining Kanker Paru dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-10-0']", True)
        self.page.locator('[id="rowfrm000041"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "kanker_paru")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.required(data, "keluarga_kanker")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.required(data, "riwayat_merokok")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.required(data, "tempat_kerja_karsinogenik")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.required(data, "tempat_tinggal_potensi_tinggi")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.required(data, "lingkungan_tidak_sehat")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.required(data, "penyakit_paru_kronik")
        ).first.click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.required(data, "foto_torax")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kanker Paru selesai")

    def do_catin_perempuan(self, data: dict, row_number: int) -> None:
        print("Skrining Catin Perempuan dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-10-0']", True)
        self.page.locator('[id="rowfrm000205"]').click()
        self.page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(
            self.required(data, "hemoglobin")
        )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Catin Perempuan selesai")

    def do_hiv(self, data: dict, row_number: int) -> None:
        print("Skrining HIV dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-11-0']", True)
        self.page.locator('[id="rowfrm000188"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "rapid_test")
        ).first.click()
        if data["rapid_test"] == "Reaktif":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.required(data, "r2_hiv")
            ).first.click()
            if data["r2_hiv"] == "Reaktif":
                self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                    has_text=self.required(data, "r3_hiv")
                ).first.click()
            elif data["r2_hiv"] == "Non Reaktif":
                self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                    has_text=self.required(data, "r1_hiv_ulang")
                ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining HIV selesai")

    def do_sifilis(self, data: dict, row_number: int) -> None:
        print("Skrining Sifilis dimulai")
        # do_pemeriksaan_check(page, "label[for='hasil-lab-11-1']", True)
        self.page.locator('[id="rowfrm000191"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.required(data, "rapid_test_sifilis")
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Sifilis selesai")
