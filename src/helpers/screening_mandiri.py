class ScreeningMandiri:
    def __init__(self, page, formatter):
        self.page = page
        self.formatter = formatter

    def do_demografi_dewasa(self, data: dict, row_number: int) -> None:
        print("Skrining Demografi Dewasa Dimulai")

        self.page.locator('[id="rowfrm000006"]').click()

        self.page.locator("label").filter(
            has_text=self.formatter(data["status_perkawinan"])
        ).click()

        if data["status_perkawinan"] != "Menikah":
            self.page.locator("label").filter(
                has_text=self.formatter(data["rencana_menikah"])
            ).click()

        self.page.locator("label").filter(
            has_text=self.formatter(data["disabilitas"])
        ).click()

        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Dewasa Selesai")

    def do_demografi_dewasa_perempuan(self, data: dict, row_number: int) -> None:
        print("Skrining Demografi Dewasa Perempuan Dimulai")
        self.page.locator('[id="rowfrm000007"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["status_perkawinan"])
        ).first.click()
        if data["status_perkawinan"] != "Menikah":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.formatter(data["rencana_menikah"])
            ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.formatter(data["sedang_hamil"])
        ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.formatter(data["disabilitas"])
        ).first.click()
        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Dewasa Perempuan Selesai")

    def do_demografi_lansia(self, data: dict, row_number: int) -> None:
        print("Skrining Demografi Lansia Dimulai")
        self.page.locator('[id="rowfrm000007"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["status_perkawinan"])
        ).first.click()

        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.formatter(data["disabilitas"])
        ).first.click()

        self.page.locator("input:has-text('Kirim')").click()

        print("Skrining Demografi Lansia Selesai")

    def do_risiko_kanker_usus(self, data: dict, row_number: int) -> None:
        print("Skrining Risiko Kanker Usus Dimulai")
        self.page.locator('[id="rowfrm000027"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["keluarga_kanker_usus"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.formatter(data["merokok"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko Kanker Usus Selesai")

    def do_risiko_tb(self, data: dict, row_number: int) -> None:
        print("Skrining Risiko TB Dimulai")
        self.page.locator('[id="rowfrm000180"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["batuk_tidak_sembuh"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Risiko Kanker Usus Selesai")

    def do_hati(self, data: dict, row_number: int) -> None:
        print("Skrining Hati Dimulai")
        self.page.locator('[id="rowfrm000028"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["hati_hepatitis_b"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.formatter(data["ibu_hepatitis_b"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.formatter(data["seks_bukan_pasangan"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.formatter(data["transfusi_darah"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.formatter(data["hemodialisis"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.formatter(data["pengguna_narkoba"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
            has_text=self.formatter(data["odhiv"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.formatter(data["hati_hepatitis_c"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
            has_text=self.formatter(data["kolesterol_tinggi"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Hati Selesai")

    def do_leher_rahim(self, data: dict, row_number: int) -> None:
        print("Skrining Kanker Leher Rahim Dimulai")
        self.page.locator('[id="rowfrm000088"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["pernah_seks"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kanker Leher Rahim Selesai")

    def do_keswa(self, data: dict, row_number: int) -> None:
        print("Skrining Kesehatan Jiwa Dimulai")
        self.page.locator('[id="rowfrm000067"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["tidak_bersemangat"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=self.formatter(data["merasa_tertekan"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.formatter(data["gugup_cemas"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.formatter(data["khawatir"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kesehatan Jiwa Selesai")

    def do_risiko_kanker_paru(self, data: dict, row_number: int) -> None:
        print("Skrining Kanker Paru Dimulai")
        self.page.locator('[id="rowfrm000138"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["merokok_setahun_terakhir"])
        ).click()
        if data["merokok_setahun_terakhir"] == "Tidak":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.formatter(data["merokok_15_tahun"])
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
                has_text=self.formatter(data["terpapar_rokok"])
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
                has_text=self.formatter(data["kanker_paru_keluarga"])
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.formatter(data["gejala_batuk"])
            ).click()
            self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
                has_text=self.formatter(data["tbc"])
            ).click()

        self.page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=self.formatter(data["terpapar_rokok"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=self.formatter(data["kanker_paru_keluarga"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=self.formatter(data["gejala_batuk"])
        ).click()
        self.page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=self.formatter(data["tbc"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Kanker Paru Selesai")

    def do_perilaku_merokok(self, data: dict, row_number: int) -> None:
        print("Skrining Perilaku Merokok Dimulai")
        self.page.locator('[id="rowfrm000064"]').click()
        self.page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
            has_text=self.formatter(data["merokok_setahun_terakhir_b"])
        ).click()

        if data["merokok_setahun_terakhir_b"] == "Ya":
            self.page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
                has_text=self.formatter(data["jenis_rokok"])
            ).click()
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.formatter(data["berapa_tahun"])
            )
            self.page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
                self.formatter(data["berapa_batang"])
            )

        elif data["merokok_setahun_terakhir_b"] == "Tidak":
            self.page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
                has_text=self.formatter(data["pernah_merokok"])
            ).click()
            if data["pernah_merokok"] == "Ya":
                self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                    self.formatter(data["berapa_tahun_sebelumnya"])
                )
                self.page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                    has_text=self.formatter(data["kapan_berhenti"])
                ).click()
        self.page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
            has_text=self.formatter(data["terpapar_sebulan_terakhir"])
        ).click()
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Perilaku Merokok Selesai")

    def do_aktivitas_fisik(self, data: dict, row_number: int) -> None:
        print("Skrining Aktivitas Fisik Dimulai")
        self.page.locator('[id="rowfrm000169"]').click()

        self.page.locator("div[aria-controls='sq_100i_list']").click()
        self.page.locator("#sq_100i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_domestik"])).click()
        if data["aktivitas_domestik"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
                self.formatter(data["hari_domestik"])
            )
            self.page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
                self.formatter(data["menit_domestik"])
            )

        self.page.locator("div[aria-controls='sq_103i_list']").click()
        self.page.locator("#sq_103i .sd-dropdown__value").click()
        self.page.locator("#sq_103i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_pekerjaan"])).click()
        if data["aktivitas_pekerjaan"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
                self.formatter(data["hari_pekerjaan"])
            )
            self.page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                self.formatter(data["menit_pekerjaan"])
            )

        self.page.locator("div[aria-controls='sq_106i_list']").click()
        self.page.locator("#sq_106i .sd-dropdown__value").click()
        self.page.locator("#sq_106i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_perjalanan"])).click()
        if data["aktivitas_perjalanan"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_107_ariaTitle']").fill(
                self.formatter(data["hari_perjalanan"])
            )
            self.page.locator("input[aria-labelledby='sq_108_ariaTitle']").fill(
                self.formatter(data["menit_perjalanan"])
            )

        self.page.locator("div[aria-controls='sq_109i_list']").click()
        self.page.locator("#sq_109i .sd-dropdown__value").click()
        self.page.locator("#sq_109i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_olahraga"])).click()
        if data["aktivitas_olahraga"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_110_ariaTitle']").fill(
                self.formatter(data["hari_olahraga"])
            )
            self.page.locator("input[aria-labelledby='sq_111_ariaTitle']").fill(
                self.formatter(data["menit_olahraga"])
            )

        self.page.locator("div[aria-controls='sq_112i_list']").click()
        self.page.locator("#sq_112i .sd-dropdown__value").click()

        self.page.locator("#sq_112i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_kerja_berat"])).click()
        if data["aktivitas_kerja_berat"] == "Ya":
            self.page.locator("input[aria-labelledby='sq_113_ariaTitle']").fill(
                self.formatter(data["hari_kerja_berat"])
            )
            self.page.locator("input[aria-labelledby='sq_114_ariaTitle']").fill(
                self.formatter(data["menit_kerja_berat"])
            )

        self.page.locator("div[aria-controls='sq_115i_list']").click()
        self.page.locator("#sq_115i .sd-dropdown__value").click()
        self.page.locator("#sq_115i_list [role='option']").filter(
            has_text=self.formatter(data["aktivitas_olahraga_berat"])).click()
        if data["aktivitas_olahraga_berat"] == "Ya":
            page.locator("input[aria-labelledby='sq_116_ariaTitle']").fill(
                self.formatter(data["hari_olahraga_berat"])
            )
            page.locator("input[aria-labelledby='sq_117_ariaTitle']").fill(
                self.formatter(data["menit_olahraga_berat"])
            )
        self.page.locator("input:has-text('Kirim')").click()
        print("Skrining Aktivitas Fisik Selesai")
