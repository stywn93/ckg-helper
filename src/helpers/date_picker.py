# src/ckg_helper/date_picker.py
from click_delay import no_click_delay

class DatePicker:
    MONTH_LABELS = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "Mei", "06": "Jun", "07": "Jul", "08": "Agt",
        "09": "Sep", "10": "Okt", "11": "Nov", "12": "Des",
    }

    MONTH_TO_NUMBER = {label: index for index, label in enumerate(MONTH_LABELS.values(), start=1)}

    def select(self, trigger_locator, date_value: str):
        with no_click_delay():
            year, month, _day = date_value.split("-")
            target_year = int(year)
            target_month = int(month)
            month_label = self.MONTH_LABELS[month]

            trigger_locator.click()
            page = trigger_locator.page
            popup = page.locator(".mx-datepicker-popup").last

            month_btn = popup.locator(".mx-btn-current-month")
            year_btn = popup.locator(".mx-btn-current-year")
            prev_year = popup.locator(".mx-btn-icon-double-left")
            prev_month = popup.locator(".mx-btn-icon-left")
            next_month = popup.locator(".mx-btn-icon-right")

            while int(year_btn.text_content().strip()) != target_year:
                current_year = int(year_btn.text_content().strip())
                if target_year < current_year:
                    prev_year.click()
                else:
                    break

            while month_btn.text_content().strip() != month_label:
                current_month = self.MONTH_TO_NUMBER[month_btn.text_content().strip()]
                if target_month < current_month:
                    prev_month.click()
                else:
                    next_month.click()
                page.wait_for_timeout(300)

            popup.locator(f'td.cell[title="{date_value}"]').click()
