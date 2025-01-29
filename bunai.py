# -*- coding: utf-8 -*-

# BunAI 
#
# Copyright (C) 2025  William N. (willdoesprojects)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://github.com/willdoesprojects>.
#
# Any modifications to this file must keep this entire header intact.

from aqt import mw
from aqt.qt import (QSettings, QAction, QWidget, QTabWidget, QVBoxLayout, 
                    QLabel, QPushButton, QHBoxLayout, QLineEdit, QDialog, 
                    QComboBox, QSizePolicy, Qt, QProgressBar, QApplication,
                    QThreadPool)
import time
import threading
from . import sentence_worker

class BunAI:
    def __init__(self, mw) -> None:
        if mw:
            self.settings = QSettings()
            self.stop_event = threading.Event()

            self.mw = mw
            self.menu_action = QAction("BunAI", mw)
            self.menu_action.triggered.connect(self.setup)
            mw.form.menuTools.addAction(self.menu_action)

            self.deck = self.settings.value("deck", "")

            self.sentence_field = self.settings.value(f"{self.deck}_sentence_field", "")
            self.translation_field = self.settings.value(f"{self.deck}_translation_field", "")
            self.diffculty = self.settings.value(f"{self.deck}_diffculty_field", "")
            self.language = self.settings.value("language", "")
    def setup(self) -> None:
        # Tab Section
        tab_widget = QTabWidget()
        """ General Tab Section """
        
        # Intialize General Tab Layout
        general_tab = QWidget()
        self.general_layout = QVBoxLayout()
        general_tab.setLayout(self.general_layout)
        
        # Create Deck Dropdown Menu
        deck_names = [deck.name for deck in mw.col.decks.all_names_and_ids()]         

        for name in deck_names[:]:
            deck_id = mw.col.decks.id(name)
            card_ids = mw.col.decks.cids(deck_id)
            
            if not card_ids:
                deck_names.remove(name)
                continue
        
        # If no decks or decks with any fields exisit, then no layouts will present it self 
        if not deck_names:
            self.general_layout.addWidget(QLabel("You either have no Decks or no Decks with Any Fields! Please either create Decks or create Fields to get Started!"))
        # Proceed with Adding the Deck Dropdown, Sentence Field Dropdown, Translation Field Dropdown, and Diffculty Dropdown 
        else:
            self.general_layout.addWidget(QLabel("Welcome to Bun AI!"))
            deck_dropdown, _ = self.create_dropdown_menu("Deck:", deck_names, self.general_layout)
            deck_dropdown.currentTextChanged.connect(self.handle_selection) 

            deck_id = mw.col.decks.id(deck_names[0])
            card_ids = mw.col.decks.cids(deck_id)
            
            card = mw.col.get_card(card_ids[0])
            note = card.note()
            model = note.note_type()
            
            # Get the fields from the model
            fields = [field["name"] for field in model["flds"]]
            
            self.sentence_dropdown, self.sentence_layout = self.create_dropdown_menu("Sentence Field:", fields, self.general_layout)
            self.translation_dropdown, self.translation_layout = self.create_dropdown_menu("Translation Field:", fields, self.general_layout)

            # Diffculty Mode
            mode = ["Beginner", "Normal", "Complex"] 
            
            self.diffculty_mode_dropdown, _ = self.create_dropdown_menu("Diffculty Setting:", mode, self.general_layout)
            
            # Preselecting the option from user's last session

            deck_index = deck_dropdown.findText(self.deck)
            if deck_index != -1:
                deck_dropdown.setCurrentIndex(deck_index)

            sentence_index = self.sentence_dropdown.findText(self.sentence_field)
            if sentence_index != -1:
                self.sentence_dropdown.setCurrentIndex(sentence_index)

            translation_index = self.translation_dropdown.findText(self.translation_field)
            if translation_index != -1:
                self.translation_dropdown.setCurrentIndex(translation_index)

            diffculty_index = self.diffculty_mode_dropdown.findText(self.diffculty)
            if diffculty_index != -1:
                self.diffculty_mode_dropdown.setCurrentIndex(diffculty_index)

            # Connect the Dropdown Menus

            self.sentence_dropdown.currentTextChanged.connect(self.set_sentence)
            self.translation_dropdown.currentTextChanged.connect(self.set_translation)
            self.diffculty_mode_dropdown.currentTextChanged.connect(self.set_diffculty)

            # Button to Generate Sentences
            generate_button = QPushButton("Generate Sentences!")
            generate_button.clicked.connect(self.popup_generate_window)

            self.general_layout.addWidget(generate_button)
        
        """ Advanced Tab """

        # Intialize Advanced Tab & Layout
        advanced_tab = QWidget()
        self.advanced_layout = QVBoxLayout()
        advanced_tab.setLayout(self.advanced_layout)
        
        # Creation of the OpenAI API Key Prompt Field
        key_layout = QHBoxLayout()
        key_label = QLabel("OpenAI API Key: ")
        key_layout.addWidget(key_label)

        # Creation of OpenAI API Key Input Textbox
        self.key_input_field = QLineEdit()
        self.key_input_field.setPlaceholderText("Enter your OpenAI API Key!")

        # Loading API Key saved from user if exisits
        self.api_key = self.settings.value("openai_api_key", "")
        self.key_input_field.setText(self.api_key)

        self.key_input_field.editingFinished.connect(self.save_key)

        key_layout.addWidget(self.key_input_field)

        self.advanced_layout.addLayout(key_layout)
        
        # Language Section
        language_layout = QHBoxLayout()
        language_label = QLabel("Language: ")
        language_layout.addWidget(language_label)

        self.language_input_field = QLineEdit()
        self.language_input_field.setPlaceholderText("Enter desired Language!")
        self.language_input_field.setText(self.language)

        self.language_input_field.editingFinished.connect(self.set_language)
        language_layout.addWidget(self.language_input_field)

        self.advanced_layout.addLayout(language_layout)

        # Add Both General & Advanced Tabs to Main Tab Widget
        tab_widget.addTab(general_tab, "General") 
        tab_widget.addTab(advanced_tab, "Advanced") 

        # Main Layout 
        dialog = QDialog(self.mw)
        dialog.setWindowTitle("BunAI")
        layout = QVBoxLayout()
        

        # Adding Tab Widget
        layout.addWidget(tab_widget)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.setLayout(layout)
        dialog.exec()
    
    def set_language(self):
        self.language = self.language_input_field.text()
        self.settings.setValue("language", self.language)

    def set_diffculty(self, field):
        self.diffculty = field
        self.settings.setValue(f"{self.deck}_diffculty_field", self.diffculty)

    def set_sentence(self, field):
        self.sentence_field = field
        self.settings.setValue(f"{self.deck}_sentence_field", self.sentence_field)

    def set_translation(self, field):
        self.translation_field = field
        self.settings.setValue(f"{self.deck}_translation_field", self.translation_field)

    def save_key(self):
        self.api_key = self.key_input_field.text()
        self.settings.setValue("openai_api_key", self.api_key)

    def handle_selection(self, text):     
        self.clear_layout() 
        self.deck = text

        self.settings.setValue("deck", self.deck)

        deck_id = mw.col.decks.id(text)
        card_ids = mw.col.decks.cids(deck_id)
        
        card = mw.col.get_card(card_ids[0])
        note = card.note()
        model = note.note_type()
            
        # Get the fields from the model
        fields = [field["name"] for field in model["flds"]]
        
        sentence_dropdown = QComboBox()
        sentence_dropdown.addItems(fields)
        sentence_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        translation_dropdown = QComboBox()
        translation_dropdown.addItems(fields)
        translation_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.sentence_dropdown = sentence_dropdown 
        self.translation_dropdown = translation_dropdown
        
        self.sentence_layout.addWidget(self.sentence_dropdown)
        self.translation_layout.addWidget(self.translation_dropdown)

        self.sentence_dropdown.currentTextChanged.connect(self.set_sentence)
        self.translation_dropdown.currentTextChanged.connect(self.set_translation)

    def clear_layout(self):
        """Clear all widgets and layouts from a layout."""
        self.sentence_dropdown.setParent(None)
        self.translation_dropdown.setParent(None)
        
    def create_dropdown_menu(self, label_name, item_names, layout):
        # Deck Field & Dropdown Menu
        deck_layout = QHBoxLayout()
        deck_label = QLabel(f"{label_name}")
        deck_layout.addWidget(deck_label)

        # Dropdown Menu
        deck_dropdown = QComboBox()
        deck_dropdown.addItems(item_names)
        deck_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        deck_layout.addWidget(deck_dropdown)

        layout.addLayout(deck_layout)
        
        return deck_dropdown, deck_layout
    
    def popup_generate_window(self):
        deck_id = mw.col.decks.id("test")
        card_ids = mw.col.decks.cids(deck_id)
        notes = []
        curr = 0
        for card_id in card_ids:
            card = mw.col.get_card(card_id)
            note = card.note()

            note[self.sentence_field] = "" 
            note[self.translation_field] = ""

            notes.append(note)

            if curr == 15:
                break
            curr += 1

            if not note[self.sentence_field] and not note[self.translation_field]:
                notes.append(note)

        total_cards = len(notes)
        """ Frontend Side """
        # Creation & Intialization of Popup Window for Generating Sentences
        popup_window = QDialog(self.mw)
        popup_window.setWindowTitle("Bun Sentence Generation")
        popup_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        popup_window.setMinimumSize(600, 200)

        # Creating Layout and Setting it to the Popup Window
        layout = QVBoxLayout()
        popup_window.setLayout(layout)

        # Intialization of Main Label
        label = QLabel("Generating Sentences:")
        layout.addWidget(label)

        # Intialization of Progress Bar
        progress_layout = QHBoxLayout()
        progress_bar = QProgressBar()

        progress_bar.setMinimum(0)
        progress_bar.setMaximum(total_cards)
        progress_bar.setTextVisible(False)
        progress_label = QLabel("0%")

        progress_layout.addWidget(progress_bar)
        progress_layout.addWidget(progress_label)
        current_progress = 0

        layout.addLayout(progress_layout)

        action_button = QPushButton("Start")
        layout.addWidget(action_button)
        """ Backend Side """
        tries = 0

        custom_css = ".defined-word {}"
        model = mw.col.models.current()
        if "defined-word" not in model["css"]:
            model["css"] += custom_css
            mw.col.models.save(model)
            mw.reset()

        def update_progress_bar():
            nonlocal current_progress
            current_progress += 1
            progress_bar.setValue(current_progress)

            percentage = int(((current_progress) / total_cards) * 100)
            progress_label.setText(f"{percentage}%")

            QApplication.processEvents()

            if percentage == 100:
                action_button.setEnabled(True)
                action_button.setText("Close")
                action_button.clicked.disconnect()
                action_button.clicked.connect(popup_window.reject)
                
                label.setText("Generation Complete!")
                print(f"Total time: {time.time() - self.time:.2f} seconds")

        def error(error_msg, i):
            nonlocal tries
            if tries == 10 and not self.stop_event.is_set():
                self.stop_event.set()
                label.setParent(None)
                progress_bar.setParent(None)
                progress_label.setParent(None)
        
                error_label = QLabel(f"{error_msg}")
                error_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;
                        text-align: center;                      
                    }
                """)
                progress_layout.addWidget(error_label)

                action_button.setEnabled(True)
                action_button.setText("Close")
                action_button.clicked.disconnect()
                action_button.clicked.connect(popup_window.reject)
            else:
                tries += i
        def run():
            self.time = time.time()
            action_button.setEnabled(False)
            pool = QThreadPool.globalInstance()

            self.stop_event.clear()
            for note in notes:
                if self.stop_event.is_set():
                    break
                generate = sentence_worker.SentenceWorker(note, self.api_key, self.diffculty, self.sentence_field, self.translation_field, self.stop_event, self.language)
                generate.signals.complete_signal.connect(update_progress_bar)
                generate.signals.error_signal.connect(error)
                pool.start(generate)
            
        action_button.clicked.connect(run)
        popup_window.show() 