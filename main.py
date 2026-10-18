
import sys
from pathlib import Path
from booklet_engine import arrange_booklet


import pymupdf

from PySide6.QtCore import Qt, QSize, QSettings, QUrl
from PySide6.QtGui import QImage, QPixmap, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QScrollArea,
    QToolButton,
    QMessageBox,
    QInputDialog,
    QSlider,
    QComboBox,
)


class BookletMaker(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("A5 Booklet Maker by Sagar Raj")
        self.resize(1000, 750)

    
        # Theme is applied dynamically after the UI is built.



        self.pdf_path = None
        self.selected_pages = set()
        self.page_buttons = []
        self.page_count = 0

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # Header and appearance controls
        header_layout = QHBoxLayout()

        self.title_label = QLabel("STARz Booklet Maker A5")
        self.title_label.setStyleSheet(
            "font-size: 25px; font-weight: 700; padding: 4px 2px;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)

        header_layout.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System Default"])
        header_layout.addWidget(self.theme_combo)

        header_layout.addWidget(QLabel("Accent"))
        self.accent_combo = QComboBox()
        # Solid accents plus two-colour gradient presets.
        self.accent_combo.addItem("Blue", "#3478F6")
        self.accent_combo.addItem("Violet", "#8250DF")
        self.accent_combo.addItem("Emerald", "#159957")
        self.accent_combo.addItem("Teal", "#0F9D9A")
        self.accent_combo.addItem("Rose", "#E64980")
        self.accent_combo.addItem("Amber", "#D97706")
        self.accent_combo.addItem("Crimson", "#DC2626")
        self.accent_combo.addItem("Indigo", "#4F46E5")
        self.accent_combo.addItem("Ocean Gradient", "#00B4DB")
        self.accent_combo.addItem("Sunset Gradient", "#FF5F6D")
        self.accent_combo.addItem("Aurora Gradient", "#00B09B")
        self.accent_combo.addItem("Berry Gradient", "#8E2DE2")
        self.accent_combo.addItem("Fire Gradient", "#F12711")
        self.accent_combo.addItem("Cotton Candy Gradient", "#F953C6")
        header_layout.addWidget(self.accent_combo)

        main_layout.addLayout(header_layout)

        self.open_button = QPushButton("Open PDF")
        self.open_button.clicked.connect(self.open_pdf)
        main_layout.addWidget(self.open_button)

        self.file_label = QLabel("No PDF selected")
        self.file_label.setWordWrap(True)
        main_layout.addWidget(self.file_label)

        # MEAW Thumbnail quality control

    
        # Thumbnail quality controls
        quality_layout = QHBoxLayout()

        quality_title = QLabel("Thumbnail Quality:")
        self.quality_value_label = QLabel("30%")

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setSingleStep(10)
        self.quality_slider.setPageStep(10)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.setTickPosition(
            QSlider.TickPosition.TicksBelow
        )
        self.quality_slider.setValue(30)
        self.quality_slider.valueChanged.connect(
            self.thumbnail_quality_changed
        )

        quality_layout.addWidget(quality_title)
        quality_layout.addWidget(self.quality_slider, 1)
        quality_layout.addWidget(self.quality_value_label)

        main_layout.addLayout(quality_layout)

        # ENDED Meaw

        controls = QHBoxLayout()

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_selection)

        self.odd_button = QPushButton("Odd")
        self.odd_button.clicked.connect(self.select_odd)

        self.even_button = QPushButton("Even")
        self.even_button.clicked.connect(self.select_even)

        self.range_button = QPushButton("Select Range")
        self.range_button.clicked.connect(self.select_range)

        self.specific_button = QPushButton("Specific Pages")
        self.specific_button.clicked.connect(self.select_specific)
        self.generate_button = QPushButton("Generate Booklet PDF")
        self.generate_button.clicked.connect(self.generate_booklet)

        for button in (
            self.select_all_button,
            self.clear_button,
            self.odd_button,
            self.even_button,
            self.range_button,
            self.specific_button,
            self.generate_button,
        ):
            controls.addWidget(button)

        main_layout.addLayout(controls)

        self.selection_label = QLabel("Selected: 0 / 0 pages")
        self.selection_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 5px;"
        )
        main_layout.addWidget(self.selection_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.thumbnail_container = QWidget()
        self.thumbnail_grid = QGridLayout(self.thumbnail_container)
        self.thumbnail_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.thumbnail_grid.setSpacing(12)

        self.scroll_area.setWidget(self.thumbnail_container)
        main_layout.addWidget(self.scroll_area)

        # Developer contact footer
        contact_layout = QHBoxLayout()
        contact_title = QLabel("Developer:")
        contact_title.setStyleSheet("font-weight: 600;")
        contact_layout.addWidget(contact_title)

        self.github_link = QPushButton("GitHub")
        self.github_link.setToolTip("Open GitHub profile")
        self.github_link.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/starzsagar")
            )
        )

        self.instagram_link = QPushButton("Instagram")
        self.instagram_link.setToolTip("Open Instagram profile")
        self.instagram_link.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://instagram.com/starz_sagar")
            )
        )

        self.linkedin_link = QPushButton("LinkedIn")
        self.linkedin_link.setToolTip("Open LinkedIn profile")
        self.linkedin_link.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://www.linkedin.com/in/starzsagar")
            )
        )

        for contact_button in (
            self.github_link,
            self.instagram_link,
            self.linkedin_link,
        ):
            contact_layout.addWidget(contact_button)

        contact_layout.addStretch(1)
        main_layout.addLayout(contact_layout)

        self.set_controls_enabled(False)

        self.settings = QSettings("STARz", "BookletMakerV1")
        saved_theme = self.settings.value("theme", "Light")
        saved_accent = self.settings.value("accent", "#3478F6")

        theme_index = self.theme_combo.findText(saved_theme)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)

        accent_index = self.accent_combo.findData(saved_accent)
        self.accent_combo.setCurrentIndex(accent_index if accent_index >= 0 else 0)

        self.theme_combo.currentTextChanged.connect(self.theme_changed)
        self.accent_combo.currentIndexChanged.connect(self.accent_changed)
        self.apply_theme()


    def theme_changed(self, theme_name):
        self.settings.setValue("theme", theme_name)
        self.apply_theme()

    def accent_changed(self, index):
        self.settings.setValue("accent", self.accent_combo.currentData())
        self.apply_theme()

    def apply_theme(self):
        theme_name = self.theme_combo.currentText()
        accent_name = self.accent_combo.currentText()
        accent = self.accent_combo.currentData() or "#3478F6"

        # Each gradient uses two coordinated colours. Solid accents remain
        # available for users who prefer a simpler, flatter interface.
        gradients = {
            "Ocean Gradient": ("#00B4DB", "#0083B0"),
            "Sunset Gradient": ("#FF5F6D", "#FFC371"),
            "Aurora Gradient": ("#00B09B", "#96C93D"),
            "Berry Gradient": ("#8E2DE2", "#4A00E0"),
            "Fire Gradient": ("#F12711", "#F5AF19"),
            "Cotton Candy Gradient": ("#F953C6", "#B91D73"),
        }
        gradient = gradients.get(accent_name)
        if gradient:
            accent_background = (
                f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {gradient[0]}, stop:1 {gradient[1]})"
            )
            gradient_hover = (
                f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {gradient[1]}, stop:1 {gradient[0]})"
            )
        else:
            accent_background = accent
            gradient_hover = accent

        # System Default follows the current Qt/Windows application palette.
        if theme_name == "System Default":
            system_window = QApplication.palette().color(
                QApplication.palette().Window
            )
            dark = system_window.lightness() < 128
        else:
            dark = theme_name == "Dark"

        if dark:
            bg = "#171A21"
            panel = "#222733"
            text = "#E8ECF3"
            muted = "#AAB4C5"
            border = "#3A4353"
            hover = "#30394A"
            disabled_bg = "#292F3A"
            disabled_text = "#737E90"
            selected_bg = "#253B31"
            thumb_bg = "#252B36"
        else:
            bg = "#F4F6FA"
            panel = "#FFFFFF"
            text = "#202938"
            muted = "#657187"
            border = "#D5DCE7"
            hover = "#EAF2FF"
            disabled_bg = "#ECEFF4"
            disabled_text = "#9AA3B2"
            selected_bg = "#E8F5E9"
            thumb_bg = "#F5F5F5"

        # Calculate a slightly darker accent for hover/pressed states.
        def darken(hex_color, factor=0.82):
            value = hex_color.lstrip("#")
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            return "#{:02X}{:02X}{:02X}".format(
                int(r * factor), int(g * factor), int(b * factor)
            )

        accent_hover = darken(accent, 0.88)
        accent_pressed = darken(accent, 0.72)
        if not gradient:
            accent_background = accent
            gradient_hover = accent_hover
        accent_pressed_background = accent_pressed

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                color: {text};
                font-family: "Segoe UI";
                font-size: 10pt;
            }}
            QLabel {{
                background: transparent;
                color: {text};
            }}
            QComboBox {{
                background-color: {panel};
                color: {text};
                border: 1px solid {border};
                border-radius: 7px;
                padding: 6px 9px;
                min-width: 92px;
            }}
            QComboBox:hover {{
                border-color: {accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {panel};
                color: {text};
                selection-background-color: {accent};
                selection-color: white;
                border: 1px solid {border};
            }}
            QPushButton {{
                background-color: {panel};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 9px 14px;
                min-height: 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
                border-color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent_hover};
                color: white;
            }}
            QPushButton:disabled {{
                color: {disabled_text};
                background-color: {disabled_bg};
                border-color: {border};
            }}
            QScrollArea {{
                background-color: {panel};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 6px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {panel};
            }}
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {border};
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_hover};
            }}
            QToolTip {{
                background-color: {panel};
                color: {text};
                border: 1px solid {border};
                padding: 5px;
            }}
        """)

        if gradient:
            self.title_label.setStyleSheet(f"""
                font-size: 25px;
                font-weight: 700;
                color: {text};
                padding: 7px 12px;
                border-left: 5px solid {gradient[0]};
                border-radius: 6px;
            """)
        else:
            self.title_label.setStyleSheet(
                f"font-size: 25px; font-weight: 700; color: {text}; padding: 4px 2px;"
            )
        self.generate_button.setStyleSheet(f"""
            QPushButton {{
                background: {accent_background};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {gradient_hover}; }}
            QPushButton:pressed {{ background-color: {accent_pressed_background}; }}
            QPushButton:disabled {{
                background-color: {border};
                color: {disabled_text};
            }}
        """)

        # Theme the thumbnail cards without changing the PDF preview itself.
        for button in self.page_buttons:
            button.setStyleSheet(f"""
                QToolButton {{
                    border: 2px solid {border};
                    border-radius: 7px;
                    padding: 5px;
                    background-color: {thumb_bg};
                    color: {text};
                    font-weight: 500;
                }}
                QToolButton:checked {{
                    border: 3px solid {accent};
                    background-color: {selected_bg};
                    color: {text};
                }}
                QToolButton:hover {{
                    border-color: {accent};
                }}
            """)

    def set_controls_enabled(self, enabled):
        for button in (
            self.select_all_button,
            self.clear_button,
            self.odd_button,
            self.even_button,
            self.range_button,
            self.specific_button,
            self.generate_button,
        ):
            button.setEnabled(enabled)


    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a PDF",
            "",
            "PDF Files (*.pdf)",
        )

        if not file_path:
            return

        try:
            thumbnails = []

            with pymupdf.open(file_path) as document:
                if len(document) == 0:
                    QMessageBox.warning(
                        self, "Empty PDF", "This PDF contains no pages."
                    )
                    return

                for page in document:
                    quality = self.quality_slider.value() / 100
                    pix = page.get_pixmap(

                                # THUMBNAIL Sharpness  SIZE here below

                        #matrix=pymupdf.Matrix(1.2, 1.2),
                        
                        matrix=pymupdf.Matrix(quality, quality),
                        alpha=False,
                    )

                    image = QImage(
                        pix.samples,
                        pix.width,
                        pix.height,
                        pix.stride,
                        QImage.Format.Format_RGB888,
                    ).copy()

                    thumbnails.append(QPixmap.fromImage(image))

                page_count = len(document)

            self.pdf_path = file_path
            self.page_count = page_count
            self.selected_pages = set(range(page_count))

            self.file_label.setText(
                f"File: {Path(file_path).name}\n"
                f"Total pages: {self.page_count}"
            )

            self.build_thumbnail_grid(thumbnails)
            self.set_controls_enabled(True)
            self.update_selection_count()

        except Exception as error:
            QMessageBox.critical(
                self, "PDF Error", f"Could not open PDF:\n{error}"

            )


    # Meaw billa 2


    def thumbnail_quality_changed(self, value):
        self.quality_value_label.setText(f"{value}%")

        # Nothing to refresh before a PDF is loaded.
        if not self.pdf_path:
            return

        try:
            thumbnails = []

            with pymupdf.open(self.pdf_path) as document:
                quality = value / 100

                for page in document:
                    pix = page.get_pixmap(
                        matrix=pymupdf.Matrix(quality, quality),
                        alpha=False,
                    )

                    image = QImage(
                        pix.samples,
                        pix.width,
                        pix.height,
                        pix.stride,
                        QImage.Format.Format_RGB888,
                    ).copy()

                    thumbnails.append(QPixmap.fromImage(image))

            self.build_thumbnail_grid(thumbnails)

        except Exception as error:
            QMessageBox.warning(
                self,
                "Thumbnail Error",
                f"Could not refresh thumbnails:\n{error}",
            )



    # meaw billa start pdf generation here

    
    def generate_booklet(self):
        # Get the selected source pages in their original order.
        selected_pages = sorted(self.selected_pages)

        if not selected_pages:
            QMessageBox.warning(
                self,
                "No Pages Selected",
                "Please select at least one page to include."
            )
            return

        # Ask where to save the finished booklet.
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Booklet PDF",
            "booklet_output.pdf",
            "PDF Files (*.pdf)"
        )

        if not output_path:
            return

        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        # A4 landscape dimensions in PDF points.
        a4_width = 841.8898
        a4_height = 595.2756
        half_width = a4_width / 2

        try:
            # Arrange selected pages into booklet sheets.
            sheets = arrange_booklet(selected_pages)

            with pymupdf.open(self.pdf_path) as source:
                output = pymupdf.open()

                try:
                    for front_left, front_right, back_left, back_right in sheets:

                        # Each physical sheet produces two PDF pages:
                        # front first, then back.
                        for left_page, right_page in (
                            (front_left, front_right),
                            (back_left, back_right),
                        ):
                            sheet = output.new_page(
                                width=a4_width,
                                height=a4_height
                            )

                            left_rect = pymupdf.Rect(
                                0, 0, half_width, a4_height
                            )
                            right_rect = pymupdf.Rect(
                                half_width, 0, a4_width, a4_height
                            )

                            # None represents a blank page.
                            if left_page is not None:
                                sheet.show_pdf_page(
                                    left_rect,
                                    source,
                                    left_page,
                                    keep_proportion=True
                                )

                            if right_page is not None:
                                sheet.show_pdf_page(
                                    right_rect,
                                    source,
                                    right_page,
                                    keep_proportion=True
                                )

                    output.save(output_path)

                finally:
                    output.close()

            QMessageBox.information(
                self,
                "Booklet Created",
                f"Your booklet PDF was saved successfully:\n\n"
                f"{output_path}\n\n"
                f"Selected pages: {len(selected_pages)}\n"
                f"Output PDF pages: {len(sheets) * 2}\n"
                f"Paper size: A4 landscape"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Could not generate the booklet:\n\n{error}"
            )

    def build_thumbnail_grid(self, thumbnails):
        while self.thumbnail_grid.count():
            item = self.thumbnail_grid.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.page_buttons = []

        for index, pixmap in enumerate(thumbnails):
            button = QToolButton()
            button.setCheckable(True)
            button.setChecked(index in self.selected_pages)
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextUnderIcon
            )
            button.setText(f"Page {index + 1}")
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(140, 185))
            #button.setFixedSize(150, 205)

            button.setStyleSheet("""
                QToolButton {
                    border: 2px solid #b8b8b8;
                    border-radius: 6px;
                    padding: 5px;
                    background: #f5f5f5;
                    color: #202020;
                }
                QToolButton:checked {
                    border: 3px solid #238636;
                    background: #e8f5e9;
                }
                QToolButton:hover {
                    border-color: #1677cc;
                }
            """)


            button.toggled.connect(
                lambda checked, page_index=index:
                self.page_toggled(page_index, checked)
            )

            row = index // 4
            column = index % 4
            self.thumbnail_grid.addWidget(button, row, column)

            self.page_buttons.append(button)

        self.update_thumbnail_sizes()
        # Reapply the active theme to newly created thumbnail buttons.
        self.apply_theme()


# MEAW NEW THING HEREEEE


    def update_thumbnail_sizes(self):
        if not self.page_buttons:
            return

        # Available width inside the scrollable thumbnail area.
        available_width = self.scroll_area.viewport().width()

        # Keep four thumbnails per row.
        spacing = self.thumbnail_grid.spacing()
        margins = self.thumbnail_grid.contentsMargins()

        usable_width = (
            available_width
            - margins.left()
            - margins.right()
            - 3 * spacing
        )

        card_width = max(100, usable_width // 4)

        # Leave room for borders and padding around each icon.
        icon_width = max(80, card_width - 16)

        # Approximate portrait page proportions.
        icon_height = round(icon_width * 1.33)

        for button in self.page_buttons:
            button.setIconSize(QSize(icon_width, icon_height))
            button.setFixedSize(
                card_width,
                icon_height + 42
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_thumbnail_sizes()



    def page_toggled(self, page_index, checked):
        if checked:
            self.selected_pages.add(page_index)
        else:
            self.selected_pages.discard(page_index)

        self.update_selection_count()

    def select_all(self):
        self.selected_pages = set(range(self.page_count))
        self.refresh_button_states()

    def clear_selection(self):
        self.selected_pages.clear()
        self.refresh_button_states()

    def select_odd(self):
        self.selected_pages = {
            i for i in range(self.page_count) if (i + 1) % 2 == 1
        }
        self.refresh_button_states()

    def select_even(self):
        self.selected_pages = {
            i for i in range(self.page_count) if (i + 1) % 2 == 0
        }
        self.refresh_button_states()

    def parse_page_input(self, text):
        """Parse inputs such as 1-5, 8, 10-12."""
        result = set()

        try:
            parts = text.split(",")

            for part in parts:
                part = part.strip()

                if not part:
                    raise ValueError("An entry is empty.")

                if "-" in part:
                    bounds = part.split("-")

                    if len(bounds) != 2:
                        raise ValueError(f"Invalid range: {part}")

                    start = int(bounds[0].strip())
                    end = int(bounds[1].strip())

                    if start > end:
                        raise ValueError(
                            f"Range {part}: start exceeds end."
                        )

                    numbers = range(start, end + 1)
                else:
                    numbers = [int(part)]

                for page_number in numbers:
                    if not 1 <= page_number <= self.page_count:
                        raise ValueError(
                            f"Page {page_number} is outside the "
                            f"valid range 1-{self.page_count}."
                        )

                    result.add(page_number - 1)

        except ValueError as error:
            raise ValueError(str(error)) from error

        if not result:
            raise ValueError("Enter at least one page number.")

        return result

    def ask_for_pages(self, title, prompt):
        text, accepted = QInputDialog.getText(
            self,
            title,
            f"{prompt}\nValid pages: 1-{self.page_count}",
        )

        if not accepted:
            return

        try:
            self.selected_pages = self.parse_page_input(text)
            self.refresh_button_states()

        except ValueError as error:
            QMessageBox.warning(
                self, "Invalid Page Selection", str(error)
            )

    def select_range(self):
        self.ask_for_pages(
            "Select Page Range",
            "Enter ranges or pages (example: 1-20, 25-30):",
        )

    def select_specific(self):
        self.ask_for_pages(
            "Select Specific Pages",
            "Enter page numbers (example: 2, 5, 8, 11):",
        )

    def refresh_button_states(self):
        for index, button in enumerate(self.page_buttons):
            button.blockSignals(True)
            button.setChecked(index in self.selected_pages)
            button.blockSignals(False)

        self.update_selection_count()

    def update_selection_count(self):
        self.selection_label.setText(
            f"Selected: {len(self.selected_pages)} / "
            f"{self.page_count} pages"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookletMaker()
    window.show()
    sys.exit(app.exec())
