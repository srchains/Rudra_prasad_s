import sys
import os
from PIL import Image

# Add current directory to path to import catdb
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QGridLayout, QScrollArea, QPushButton, QFileDialog, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTextEdit, QListWidget, QListWidgetItem, QInputDialog, QAbstractItemView,
    QTabWidget, QStyledItemDelegate, QDoubleSpinBox, QLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QRect, QPoint
from PySide6.QtGui import QPixmap, QMouseEvent, QIcon, QPainter, QFont, QPen

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=10, hSpacing=10, vSpacing=10):
        super().__init__(parent)
        self._item_list = []
        self._h_space = hSpacing
        self._v_space = vSpacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        while self.takeAt(0):
            pass

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        return self._h_space

    def verticalSpacing(self):
        return self._v_space

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x, y = rect.x(), rect.y()
        lineHeight = 0

        for item in self._item_list:
            spaceX = self.horizontalSpacing()
            spaceY = self.verticalSpacing()

            sw = item.sizeHint().width()
            sh = item.sizeHint().height()

            nextX = x + sw + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + sw + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), QSize(sw, sh)))

            x = nextX
            lineHeight = max(lineHeight, sh)

        return y + lineHeight - rect.y()

import catdb


# -------- PRICE DELEGATE --------
class PriceDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setMinimum(0.0)
        editor.setMaximum(100000.0)
        editor.setDecimals(2)
        editor.setButtonSymbols(QDoubleSpinBox.NoButtons)
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            editor.setValue(float(value))
        except (ValueError, TypeError):
            editor.setValue(0.0)
            
    def setModelData(self, editor, model, index):
        editor.interpretText()
        model.setData(index, str(editor.value()), Qt.EditRole)


# -------- CLICKABLE LABEL --------
class ClickableLabel(QLabel):
    def __init__(self, parent=None, click_callback=None):
        super().__init__(parent)
        self.click_callback = click_callback

    def mousePressEvent(self, event: QMouseEvent):
        if self.click_callback:
            self.click_callback()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Catalogue Manager")
        self.resize(1200, 700)

        catdb.init_db()

        self.main_widget = QWidget()
        main_layout = QVBoxLayout()

        # ---------------- GLOBAL SEARCH BAR ----------------
        top_search_layout = QHBoxLayout()
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("Global Search (Filters Variants & Media)...")
        self.global_search_input.setStyleSheet("padding: 8px; font-size: 14px; border: 2px solid #ddd; border-radius: 5px;")
        self.global_search_input.textChanged.connect(self.on_global_search)
        top_search_layout.addWidget(self.global_search_input)

        self.show_all_media_btn = QPushButton("Show Complete Media List")
        self.show_all_media_btn.clicked.connect(self.show_all_media)
        self.show_all_media_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; background-color: #2196F3; color: white; border-radius: 5px; } QPushButton:hover { background-color: #1976D2; }")
        top_search_layout.addWidget(self.show_all_media_btn)

        main_layout.addLayout(top_search_layout)

        splitter = QSplitter(Qt.Horizontal)

        # ---------------- LEFT PANEL - CATALOGUE DESIGNS ----------------
        self.left_widget = QWidget()
        left_layout = QVBoxLayout()

        title = QLabel("Design Catalogue")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        left_layout.addWidget(title)

        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.grid_container = QWidget()
        self.grid_layout = FlowLayout()
        self.grid_container.setLayout(self.grid_layout)

        self.scroll.setWidget(self.grid_container)
        left_layout.addWidget(self.scroll)

        self.left_widget.setLayout(left_layout)

        # ---------------- RIGHT PANEL - SPLIT INTO TWO ROWS ----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Row 1: Variants
        variants_frame = QFrame()
        variants_frame.setFrameStyle(QFrame.Box)
        variants_layout = QVBoxLayout()

        variants_title = QLabel("Variants")
        variants_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        variants_layout.addWidget(variants_title)

        # Buttons for variants
        buttons_layout = QHBoxLayout()
        self.add_variant_btn = QPushButton("Add Variant")
        self.add_variant_btn.clicked.connect(self.add_variant)
        self.add_variant_btn.setStyleSheet("QPushButton { padding: 5px; font-weight: bold; background-color: #4CAF50; color: white; border-radius: 3px; } QPushButton:hover { background-color: #45a049; }")
        
        self.edit_variant_btn = QPushButton("Edit Variant")
        self.edit_variant_btn.clicked.connect(self.edit_variant)
        self.edit_variant_btn.setStyleSheet("QPushButton { padding: 5px; font-weight: bold; background-color: #2196F3; color: white; border-radius: 3px; } QPushButton:hover { background-color: #1e88e5; }")
        
        self.update_variant_btn = QPushButton("Update Variant")
        self.update_variant_btn.clicked.connect(self.update_variant_from_table)
        self.update_variant_btn.setStyleSheet("QPushButton { padding: 5px; font-weight: bold; background-color: #FF9800; color: white; border-radius: 3px; } QPushButton:hover { background-color: #fb8c00; }")
        
        self.delete_variant_btn = QPushButton("Delete Variant")
        self.delete_variant_btn.clicked.connect(self.delete_variant)
        self.delete_variant_btn.setStyleSheet("QPushButton { padding: 5px; font-weight: bold; background-color: #F44336; color: white; border-radius: 3px; } QPushButton:hover { background-color: #e53935; }")
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_variant_btn)
        buttons_layout.addWidget(self.edit_variant_btn)
        buttons_layout.addWidget(self.update_variant_btn)
        buttons_layout.addWidget(self.delete_variant_btn)
        variants_layout.addLayout(buttons_layout)

        # Variants table
        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(6)
        self.variants_table.setHorizontalHeaderLabels(["ID", "Name", "Code ID", "Weight", "Length", "Price"])
        self.variants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.variants_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.variants_table.itemSelectionChanged.connect(self.on_variant_selected)
        self.variants_table.setItemDelegateForColumn(5, PriceDelegate(self.variants_table))
        variants_layout.addWidget(self.variants_table)

        variants_frame.setLayout(variants_layout)
        right_layout.addWidget(variants_frame)

        # Row 2: Media - Tabs for Production Media and Own Shoot
        media_frame = QFrame()
        media_frame.setFrameStyle(QFrame.Box)
        media_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        media_title = QLabel("Media")
        media_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(media_title)
        top_layout.addStretch()

        self.add_media_btn = QPushButton("Add Media")
        self.add_media_btn.clicked.connect(self.add_media)
        self.add_media_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; background-color: #FF9800; color: white; }")
        top_layout.addWidget(self.add_media_btn)

        self.delete_media_btn = QPushButton("Delete Media")
        self.delete_media_btn.clicked.connect(self.delete_selected_media)
        self.delete_media_btn.setStyleSheet("QPushButton { padding: 8px; font-weight: bold; background-color: #F44336; color: white; }")
        top_layout.addWidget(self.delete_media_btn)

        media_layout.addLayout(top_layout)

        self.media_search_input = QLineEdit()
        self.media_search_input.setPlaceholderText("Search media by description or filename...")
        self.media_search_input.setStyleSheet("padding: 8px; font-size: 14px; border: 2px solid #ddd; border-radius: 5px;")
        self.media_search_input.textChanged.connect(self.refresh_media_list)
        media_layout.addWidget(self.media_search_input)

        self.media_tabs = QTabWidget()
        
        self.reference_media_list = QListWidget()
        self.reference_media_list.setViewMode(QListWidget.IconMode)
        self.reference_media_list.setIconSize(QSize(250, 250))
        self.reference_media_list.setResizeMode(QListWidget.Adjust)
        self.reference_media_list.setSpacing(10)
        self.reference_media_list.itemDoubleClicked.connect(self.view_media)
        self.reference_media_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reference_media_list.customContextMenuRequested.connect(self.show_media_context_menu)
        
        self.ownshoot_media_list = QListWidget()
        self.ownshoot_media_list.setViewMode(QListWidget.IconMode)
        self.ownshoot_media_list.setIconSize(QSize(250, 250))
        self.ownshoot_media_list.setResizeMode(QListWidget.Adjust)
        self.ownshoot_media_list.setSpacing(10)
        self.ownshoot_media_list.itemDoubleClicked.connect(self.view_media)
        self.ownshoot_media_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ownshoot_media_list.customContextMenuRequested.connect(self.show_media_context_menu)

        self.media_tabs.addTab(self.reference_media_list, "Production Media")
        self.media_tabs.addTab(self.ownshoot_media_list, "Own Shoot")
        
        media_layout.addWidget(self.media_tabs)

        media_frame.setLayout(media_layout)
        right_layout.addWidget(media_frame)

        right_widget.setLayout(right_layout)

        # ---------------- SPLITTER ----------------
        splitter.addWidget(self.left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)

        self.selected_variant_id = None
        
        # Base path for media folders (ct/images and ct/videos)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.refresh_grid()
        self.refresh_variants_table()

    def get_full_path(self, relative_path):
        """Resolves a path relative to the script directory."""
        if not relative_path:
            return ""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.base_dir, relative_path)

    def refresh_grid(self):
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        # Get variants
        variants = catdb.get_variants()
        search_text = self.global_search_input.text().lower() if hasattr(self, 'global_search_input') else ""

        for variant in variants:
            variant_id, name, code_id, weight, length, price, image_path = variant

            if search_text and search_text not in name.lower():
                continue

            # Create clickable label for image
            label = ClickableLabel()
            label.setFixedSize(150,150)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid #ddd; border-radius: 5px;")

            full_path = self.get_full_path(image_path)
            if image_path and os.path.exists(full_path):
                pixmap = QPixmap(full_path)
                label.setPixmap(pixmap.scaled(110, 110, Qt.KeepAspectRatio))
            else:
                label.setText("No Image")

            label.click_callback = lambda vid=variant_id: self.on_design_clicked(vid)

            # Add name label below image
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 12px; font-weight: bold; padding-top: 5px;")

            # Container for image and name
            container = QWidget()
            container.setFixedSize(160, 180) # Force a strict box scale
            container_layout = QVBoxLayout()
            container_layout.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(label)
            container_layout.addWidget(name_label)
            container.setLayout(container_layout)

            self.grid_layout.addWidget(container)

    def on_design_clicked(self, variant_id):
        self.selected_variant_id = variant_id
        self.refresh_media_list()

    def refresh_variants_table(self):
        variants = catdb.get_variants()
        search_text = self.global_search_input.text().lower() if hasattr(self, 'global_search_input') else ""
        
        if search_text:
            variants = [v for v in variants if (v[1] and search_text in v[1].lower()) or (v[2] and search_text in v[2].lower())]

        self.variants_table.setRowCount(len(variants))

        for row, variant in enumerate(variants):
            variant_id, name, code_id, weight, length, price, image_path = variant

            id_item = QTableWidgetItem(str(variant_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            
            name_item = QTableWidgetItem(name)

            self.variants_table.setItem(row, 0, id_item)
            self.variants_table.setItem(row, 1, name_item)
            self.variants_table.setItem(row, 2, QTableWidgetItem(code_id or ""))
            self.variants_table.setItem(row, 3, QTableWidgetItem(str(weight) if weight else ""))
            self.variants_table.setItem(row, 4, QTableWidgetItem(str(length) if length else ""))
            self.variants_table.setItem(row, 5, QTableWidgetItem(str(price) if price else ""))

    def on_variant_selected(self):
        current_row = self.variants_table.currentRow()
        if current_row >= 0:
            variant_id_item = self.variants_table.item(current_row, 0)
            if variant_id_item:
                self.selected_variant_id = int(variant_id_item.text())
                self.refresh_media_list()

    def on_global_search(self):
        self.refresh_grid()
        self.refresh_variants_table()
        self.refresh_media_list()

    def show_all_media(self):
        self.variants_table.clearSelection()
        self.selected_variant_id = None
        if hasattr(self, 'global_search_input'):
            self.global_search_input.clear()
        self.refresh_media_list()

    def refresh_media_list(self):
        self.reference_media_list.clear()
        self.ownshoot_media_list.clear()
        
        if not self.selected_variant_id:
            pass

        search_text = self.global_search_input.text().strip() if hasattr(self, 'global_search_input') else ""
        media_search_text = self.media_search_input.text().strip().lower() if hasattr(self, 'media_search_input') else ""
        
        if search_text:
            media_items = catdb.search_media(search_text)
            for media in media_items:
                media_id, variant_name, media_type, media_path, description = media
                
                if media_search_text:
                    path_str = os.path.basename(media_path).lower() if media_path else ""
                    desc_str = description.lower() if description else ""
                    if media_search_text not in path_str and media_search_text not in desc_str:
                        continue

                tab_name = "Production" if media_type == "production" else "Own Shoot"
                item_text = f"Var: {variant_name} | {tab_name} | {os.path.basename(media_path) if media_path else 'No file'}"
                if description:
                    item_text += f"\nDesc: {description}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, media_id)
                item.setTextAlignment(Qt.AlignCenter)
                
                full_path = self.get_full_path(media_path)
                if media_path and os.path.exists(full_path):
                    try:
                        if media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                            pixmap = QPixmap(250, 250)
                            pixmap.fill(Qt.lightGray)
                            painter = QPainter(pixmap)
                            painter.setPen(QPen(Qt.black))
                            painter.setFont(QFont("Arial", 20, QFont.Bold))
                            ext = os.path.splitext(media_path)[1].upper()
                            painter.drawText(pixmap.rect(), Qt.AlignCenter, f"VIDEO\n{ext}")
                            painter.end()
                            item.setIcon(QIcon(pixmap))
                        else:
                            pixmap = QPixmap(full_path)
                            if not pixmap.isNull():
                                thumbnail = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                item.setIcon(QIcon(thumbnail))
                    except:
                        pass
                
                item.setSizeHint(QSize(260, 300))
                
                if media_type == "production":
                    self.reference_media_list.addItem(item)
                else:
                    self.ownshoot_media_list.addItem(item)
        else:
            if not self.selected_variant_id:
                media_items = catdb.get_all_media()
                for media in media_items:
                    media_id, variant_name, media_type, media_path, description = media
                    
                    if media_search_text:
                        path_str = os.path.basename(media_path).lower() if media_path else ""
                        desc_str = description.lower() if description else ""
                        if media_search_text not in path_str and media_search_text not in desc_str:
                            continue

                    item_text = f"Var: {variant_name}\n{os.path.basename(media_path) if media_path else 'No file'}"
                    if description:
                        item_text += f"\n{description}"

                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, media_id)
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    full_path = self.get_full_path(media_path)
                    if media_path and os.path.exists(full_path):
                        try:
                            if media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                                pixmap = QPixmap(250, 250)
                                pixmap.fill(Qt.lightGray)
                                painter = QPainter(pixmap)
                                painter.setPen(QPen(Qt.black))
                                painter.setFont(QFont("Arial", 20, QFont.Bold))
                                ext = os.path.splitext(media_path)[1].upper()
                                painter.drawText(pixmap.rect(), Qt.AlignCenter, f"VIDEO\n{ext}")
                                painter.end()
                                item.setIcon(QIcon(pixmap))
                            else:
                                pixmap = QPixmap(full_path)
                                if not pixmap.isNull():
                                    thumbnail = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    item.setIcon(QIcon(thumbnail))
                        except:
                            pass
                    
                    item.setSizeHint(QSize(260, 300))
                    
                    if media_type == "production":
                        self.reference_media_list.addItem(item)
                    else:
                        self.ownshoot_media_list.addItem(item)
                return

            media_items = catdb.get_media(self.selected_variant_id)
            for media in media_items:
                media_id, media_type, media_path, description = media
                
                if media_search_text:
                    path_str = os.path.basename(media_path).lower() if media_path else ""
                    desc_str = description.lower() if description else ""
                    if media_search_text not in path_str and media_search_text not in desc_str:
                        continue

                item_text = f"{os.path.basename(media_path) if media_path else 'No file'}"
                if description:
                    item_text += f"\n{description}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, media_id)
                item.setTextAlignment(Qt.AlignCenter)
                
                full_path = self.get_full_path(media_path)
                if media_path and os.path.exists(full_path):
                    try:
                        if media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                            pixmap = QPixmap(250, 250)
                            pixmap.fill(Qt.lightGray)
                            painter = QPainter(pixmap)
                            painter.setPen(QPen(Qt.black))
                            painter.setFont(QFont("Arial", 20, QFont.Bold))
                            ext = os.path.splitext(media_path)[1].upper()
                            painter.drawText(pixmap.rect(), Qt.AlignCenter, f"VIDEO\n{ext}")
                            painter.end()
                            item.setIcon(QIcon(pixmap))
                        else:
                            pixmap = QPixmap(full_path)
                            if not pixmap.isNull():
                                thumbnail = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                item.setIcon(QIcon(thumbnail))
                    except:
                        pass
                
                item.setSizeHint(QSize(260, 300))
                
                if media_type == "production":
                    self.reference_media_list.addItem(item)
                else:
                    self.ownshoot_media_list.addItem(item)

    def add_variant(self):
        name, ok = QInputDialog.getText(self, "Add Variant", "Enter variant name:")
        if not ok or not name.strip():
            return

        try:
            # Get additional details
            code_id, ok1 = QInputDialog.getText(self, "Code ID", "Enter code ID:")
            if not ok1:
                return

            weight, ok2 = QInputDialog.getDouble(self, "Weight", "Enter weight:", decimals=2)
            if not ok2:
                return

            length, ok3 = QInputDialog.getDouble(self, "Length", "Enter length:", decimals=2)
            if not ok3:
                return

            price, ok4 = QInputDialog.getDouble(self, "Price", "Enter price (Max 1 Lakh):", 0.0, 0.0, 100000.0, 2)
            if not ok4:
                return
            if price > 100000:
                QMessageBox.warning(self, "Error", "Price cannot exceed 1 Lakh (100,000)!")
                return

            # Select image
            image_path, _ = QFileDialog.getOpenFileName(
                self, "Select Image for Variant", "",
                "Images (*.png *.jpg *.jpeg *.webp)"
            )
            if not image_path:
                QMessageBox.warning(self, "Error", "Image selection cancelled!")
                return

            # Convert webp to jpg if needed
            if image_path.lower().endswith(".webp"):
                img = Image.open(image_path).convert("RGB")
                webp_path = image_path
                image_path = image_path.replace(".webp", ".jpg")
                img.save(image_path, "JPEG")
                os.remove(webp_path)

            # Insert variant first
            variant_id = catdb.insert_variant(name.strip(), code_id.strip(), weight, length, price)

            # Create images folder if not exists
            images_folder = self.get_full_path("images")
            os.makedirs(images_folder, exist_ok=True)

            # Save image with variant ID
            new_image_rel_path = os.path.join("images", f"{variant_id}.jpg")
            new_image_full_path = self.get_full_path(new_image_rel_path)
            img = Image.open(image_path).convert("RGB")
            img.save(new_image_full_path, "JPEG", quality=90)

            # Update variant with relative image path
            catdb.update_image_path(variant_id, new_image_rel_path)

            self.refresh_variants_table()
            self.refresh_grid()
            QMessageBox.information(self, "Success", "Variant added successfully!")

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.warning(self, "Error", "Variant name already exists!")
            else:
                QMessageBox.critical(self, "Error", str(e))

    def edit_variant(self):
        current_row = self.variants_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a variant to edit!")
            return

        variant_id = int(self.variants_table.item(current_row, 0).text())
        current_name = self.variants_table.item(current_row, 1).text()
        current_code_id = self.variants_table.item(current_row, 2).text()
        current_weight = float(self.variants_table.item(current_row, 3).text() or 0.0)
        current_length = float(self.variants_table.item(current_row, 4).text() or 0.0)
        current_price = float(self.variants_table.item(current_row, 5).text() or 0.0)

        try:
            name, ok0 = QInputDialog.getText(self, "Edit Name", "Enter new name:", text=current_name)
            if not ok0 or not name.strip():
                return
                
            code_id, ok1 = QInputDialog.getText(self, "Edit Code ID", "Enter code ID:", text=current_code_id)
            if not ok1:
                return

            weight, ok2 = QInputDialog.getDouble(self, "Edit Weight", "Enter weight:", value=current_weight, decimals=2)
            if not ok2:
                return

            length, ok3 = QInputDialog.getDouble(self, "Edit Length", "Enter length:", value=current_length, decimals=2)
            if not ok3:
                return

            price, ok4 = QInputDialog.getDouble(self, "Edit Price", "Enter price (Max 1 Lakh):", current_price, 0.0, 100000.0, 2)
            if not ok4:
                return
            if price > 100000:
                QMessageBox.warning(self, "Error", "Price cannot exceed 1 Lakh (100,000)!")
                return

            catdb.update_variant(variant_id, name.strip(), code_id.strip(), weight, length, price)
            self.refresh_variants_table()
            self.refresh_grid()
            QMessageBox.information(self, "Success", "Variant updated successfully!")

        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.warning(self, "Error", "Variant name already exists!")
            else:
                QMessageBox.critical(self, "Error", str(e))

    def update_variant_from_table(self):
        current_row = self.variants_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a variant row to update!")
            return

        variant_id = int(self.variants_table.item(current_row, 0).text())
        
        try:
            name = self.variants_table.item(current_row, 1).text() if self.variants_table.item(current_row, 1) else ""
            if not name.strip():
                QMessageBox.warning(self, "Error", "Variant name cannot be empty!")
                return
                
            code_id = self.variants_table.item(current_row, 2).text() if self.variants_table.item(current_row, 2) else ""
            weight_text = self.variants_table.item(current_row, 3).text() if self.variants_table.item(current_row, 3) else "0.0"
            length_text = self.variants_table.item(current_row, 4).text() if self.variants_table.item(current_row, 4) else "0.0"
            price_text = self.variants_table.item(current_row, 5).text() if self.variants_table.item(current_row, 5) else "0.0"

            weight = float(weight_text or 0.0)
            length = float(length_text or 0.0)
            price = float(price_text or 0.0)
            
            if price > 100000:
                QMessageBox.warning(self, "Error", "Price cannot exceed 1 Lakh (100,000)!")
                return
            
            catdb.update_variant(variant_id, name.strip(), code_id.strip(), weight, length, price)
            self.refresh_grid()
            QMessageBox.information(self, "Success", "Variant updated directly from table!")
        except ValueError:
            QMessageBox.critical(self, "Error", "Please check your number formats (Weight, Length, Price must be numbers).")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.warning(self, "Error", "Variant name already exists or is invalid!")
            else:
                QMessageBox.critical(self, "Error", str(e))

    def delete_variant(self):
        current_row = self.variants_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a variant to delete!")
            return

        name_item = self.variants_table.item(current_row, 1)
        if not name_item:
            return

        name = name_item.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete variant '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            success = catdb.delete_variant(name)
            if success:
                self.refresh_variants_table()
                self.refresh_grid()
                self.reference_media_list.clear()
                self.ownshoot_media_list.clear()
                QMessageBox.information(self, "Success", "Variant deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", "Variant not found!")

    def add_media(self):
        if not self.selected_variant_id:
            QMessageBox.warning(self, "Error", "Please select a variant first!")
            return

        # Auto-detect media type based on selected tab
        current_tab_index = self.media_tabs.currentIndex() if hasattr(self, 'media_tabs') else 0
        media_type_db = "production" if current_tab_index == 0 else "own_shoot"

        # Select file
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "",
            "Images (*.png *.jpg *.jpeg *.webp);;Videos (*.mp4 *.avi);;All Files (*)"
        )

        if not file_path:
            return

        # Get description
        description, ok = QInputDialog.getText(self, "Description", "Enter description (optional):")
        if not ok:
            return

        try:
            # 1. Insert into DB with an empty path first to generate the stable Media ID
            media_id = catdb.insert_media(self.selected_variant_id, media_type_db, "", description)

            # 2. Setup folders
            images_folder = self.get_full_path("images")
            videos_folder = self.get_full_path("videos")
            os.makedirs(images_folder, exist_ok=True)
            import shutil
            
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                os.makedirs(videos_folder, exist_ok=True)
                new_media_rel_path = os.path.join("videos", f"{media_id}{ext}")
                new_media_full_path = self.get_full_path(new_media_rel_path)
                shutil.copy2(file_path, new_media_full_path)
            else:
                # Use the requested Variant ID format, with the Media ID appended to prevent overwrites
                new_media_rel_path = os.path.join("images", f"{self.selected_variant_id}_{media_id}.jpg")
                new_media_full_path = self.get_full_path(new_media_rel_path)
    
                # Convert to RGB and save as a high-quality JPEG
                img = Image.open(file_path)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert("RGB")
                img.save(new_media_full_path, "JPEG", quality=90)

            # 3. Update the database record with the internal relative path
            catdb.update_media_path(media_id, new_media_rel_path)
            
            self.refresh_media_list()
            QMessageBox.information(self, "Success", "Media added successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def view_media(self):
        # Check which list the current item is from
        current_item = None
        if hasattr(self, 'reference_media_list') and self.reference_media_list.currentItem():
            current_item = self.reference_media_list.currentItem()
        elif hasattr(self, 'ownshoot_media_list') and self.ownshoot_media_list.currentItem():
            current_item = self.ownshoot_media_list.currentItem()
        
        if not current_item:
            return

        media_id = current_item.data(Qt.UserRole)

        media_row = catdb.get_media_by_id(media_id)
        if media_row:
            media_id_val, media_type, media_path, description = media_row
            if media_path and os.path.exists(media_path):
                    # Create a preview window
                    preview_window = QWidget()
                    preview_window.setWindowTitle(f"{media_type.replace('_', ' ').title()} - Preview")
                    preview_layout = QVBoxLayout()

                    is_video = media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))

                    if is_video:
                        preview_label = QLabel("Video File")
                        preview_label.setAlignment(Qt.AlignCenter)
                        preview_label.setStyleSheet("font-size: 24px; font-weight: bold; min-height: 200px; border: 1px solid #ccc;")
                        preview_layout.addWidget(preview_label)
                        
                        open_btn = QPushButton("Open Video in Default Player")
                        from PySide6.QtGui import QDesktopServices
                        from PySide6.QtCore import QUrl
                        open_btn.clicked.connect(lambda checked=False, p=self.get_full_path(media_path): QDesktopServices.openUrl(QUrl.fromLocalFile(p)))
                        open_btn.setStyleSheet("padding: 10px; background-color: #4CAF50; color: white; font-weight: bold; margin-bottom: 15px;")
                        preview_layout.addWidget(open_btn)
                    else:
                        preview_label = QLabel()
                        full_path = self.get_full_path(media_path)
                        pixmap = QPixmap(full_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaledToWidth(600, Qt.SmoothTransformation)
                            preview_label.setPixmap(scaled_pixmap)
                            preview_label.setAlignment(Qt.AlignCenter)
                        preview_layout.addWidget(preview_label)

                    # Info label
                    info_text = f"Type: {media_type.replace('_', ' ').title()}\nPath: {media_path}\nDescription: {description or 'N/A'}"
                    info_label = QLabel(info_text)
                    preview_layout.addWidget(info_label)

                    # Delete button
                    delete_btn = QPushButton("Delete Media")
                    delete_btn.clicked.connect(lambda: self.delete_media_item(media_id_val, preview_window))
                    preview_layout.addWidget(delete_btn)

                    preview_window.setLayout(preview_layout)
                    preview_window.setGeometry(100, 100, 700, 600)
                    preview_window.show()

    def delete_media_item(self, media_id, window):
        reply = QMessageBox.question(None, "Confirm Delete", "Delete this media?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            catdb.delete_media(media_id)
            self.refresh_media_list()
            window.close()
            QMessageBox.information(None, "Success", "Media deleted successfully!")

    def delete_selected_media(self):
        current_list = self.reference_media_list if self.media_tabs.currentIndex() == 0 else self.ownshoot_media_list
        current_item = current_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a media item from the list to delete!")
            return

        media_id = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this media item?", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            catdb.delete_media(media_id)
            self.refresh_media_list()
            QMessageBox.information(self, "Success", "Media deleted successfully!")

    def show_media_context_menu(self, position):
        sender_list = self.sender()
        if not sender_list:
            return
        
        item = sender_list.itemAt(position)
        if not item:
            return

        # Note: For simplicity, using message box. Can be enhanced with QMenu
        QMessageBox.information(self, "Media Info", 
                               f"Double-click to view\nRight-click on item to delete via view window")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
