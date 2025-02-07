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

from typing import List
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
            return
        
        # Proceed with Adding the Deck Dropdown, Sentence Field Dropdown, Translation Field Dropdown, and Diffculty Dropdown 
        else:
            self.general_layout.addWidget(QLabel("Welcome to Bun AI!"))
            _, deck_dropdown = self.create_dropdown_menu("Deck:", deck_names)
            
            # If the deck is deleted, automatically sets it to the first one
            if self.deck not in deck_names:
                self.deck = deck_names[0]
            
            # Creation of Sentence & Translation Fields
            deck_id = mw.col.decks.id(self.deck)
            card_ids = mw.col.decks.cids(deck_id)
            
            card = mw.col.get_card(card_ids[0])
            note = card.note()
            model = note.note_type()
                
            # Intialization of Sentence and Translation Field
            fields = [field["name"] for field in model["flds"]]
            self.sentence_layout, sentence_dropdown = self.create_dropdown_menu("Sentence Field:", fields)
            self.translation_layout, translation_dropdown = self.create_dropdown_menu("Translation Field:", fields)

            sentence_dropdown.currentTextChanged.connect(self.set_sentence)
            translation_dropdown.currentTextChanged.connect(self.set_translation)

            self.sentence_field = self.settings.value(f"{self.deck}_sentence_field", "")
            self.translation_field = self.settings.value(f"{self.deck}_translation_field", "")

            # Preselection of Fields from Previous Sessions
            sentence_index = sentence_dropdown.findText(self.sentence_field)
            if sentence_index == -1:
                sentence_index = 1

            sentence_dropdown.setCurrentIndex(sentence_index)

            translation_index = translation_dropdown.findText(self.translation_field)
            if translation_index == -1:
                translation_index = 1
            translation_dropdown.setCurrentIndex(translation_index)

            # Creation Diffuclty Dropdowns
            mode = ["Beginner", "Normal", "Complex"] 
            self.diffculty_mode_layout, diffculty_mode_dropdown  = self.create_dropdown_menu("Diffculty Setting:", mode)
            
            diffculty_mode_dropdown.currentTextChanged.connect(self.set_diffculty)
            self.diffculty = self.settings.value(f"diffculty_field", "")

            diffculty_index = diffculty_mode_dropdown.findText(self.diffculty)
            if diffculty_index != -1:
                diffculty_mode_dropdown.setCurrentIndex(diffculty_index)

            # Preselection deck from user's last session
            deck_index = deck_dropdown.findText(self.deck)
            if deck_index != -1:
                deck_dropdown.setCurrentIndex(deck_index)
            deck_dropdown.currentTextChanged.connect(self.handle_selection) 

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
    
    def set_language(self) -> None:
        self.language = self.language_input_field.text()
        self.settings.setValue("language", self.language)

    def set_diffculty(self, field: str) -> None:
        self.diffculty = field
        self.settings.setValue(f"diffculty_field", self.diffculty)

    def set_sentence(self, field: str) -> None:
        self.sentence_field = field
        self.settings.setValue(f"{self.deck}_sentence_field", self.sentence_field)

    def set_translation(self, field: str) -> None:
        self.translation_field = field
        self.settings.setValue(f"{self.deck}_translation_field", self.translation_field)

    def save_key(self) -> None:
        self.api_key = self.key_input_field.text()
        self.settings.setValue("openai_api_key", self.api_key)

    def handle_selection(self, text: str) -> None:  
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

        # Reintilization of the Sentence and Dropdown Menus with Preselection
        _, sentence_dropdown = self.create_dropdown_menu("", fields)
        _, translation_dropdown = self.create_dropdown_menu("", fields)

        self.sentence_layout.addWidget(sentence_dropdown)
        self.translation_layout.addWidget(translation_dropdown)

        sentence_dropdown.currentTextChanged.connect(self.set_sentence)
        translation_dropdown.currentTextChanged.connect(self.set_translation)

        self.sentence_field = self.settings.value(f"{self.deck}_sentence_field", "")
        self.translation_field = self.settings.value(f"{self.deck}_translation_field", "")

        sentence_index = sentence_dropdown.findText(self.sentence_field)
        if sentence_index == -1:
            sentence_index = 1
        sentence_dropdown.setCurrentIndex(sentence_index)

        translation_index = translation_dropdown.findText(self.translation_field)
        if translation_index == -1:
            translation_index = 1
        translation_dropdown.setCurrentIndex(translation_index)

    def clear_layout(self) -> None:
        """Clear all widgets and layouts from a layout.""" 
        old_sentence_dropdown = self.sentence_layout.takeAt(1)
        if old_sentence_dropdown and old_sentence_dropdown.widget():
            old_sentence_dropdown.widget().deleteLater()
        
        old_translation_dropdown = self.translation_layout.takeAt(1)
        if old_translation_dropdown and old_translation_dropdown.widget():
            old_translation_dropdown.widget().deleteLater()

        
    def create_dropdown_menu(self, label_name: str, item_names: List[str]) -> None:
        # Deck Field & Dropdown Menu
        dropdown_layout = QHBoxLayout()
        dropdown_label = QLabel(f"{label_name}")
        dropdown_layout.addWidget(dropdown_label)

        # Dropdown Menu
        dropdown_menu = QComboBox()
        dropdown_menu.addItems(item_names)
        dropdown_menu.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        dropdown_layout.addWidget(dropdown_menu)
        
        if label_name:
            self.general_layout.addLayout(dropdown_layout)

        return dropdown_layout, dropdown_menu
    
    def popup_generate_window(self) -> None:
        """ Popup Window for Generating Sentences """

        # Obtain the cards from the desired fields from the desired deck
        deck_id = mw.col.decks.id(self.deck)
        card_ids = mw.col.decks.cids(deck_id)
        notes = []
        for card_id in card_ids:
            card = mw.col.get_card(card_id)
            note = card.note()

            #Both fields must be empty in order to enact change on the card
            if not note[self.sentence_field] and not note[self.translation_field]:
                notes.append(note)

        total_cards = len(notes)
        
        # Creation & Intialization of Popup Window for Generating Sentences
        popup_window = QDialog(self.mw)
        popup_window.setWindowTitle("Bun Sentence Generation")
        popup_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        popup_window.setMinimumSize(600, 200)

        # Creating Layout and Setting it to the Popup Window
        layout = QVBoxLayout()
        popup_window.setLayout(layout)

        main_label = QLabel("")
        main_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;                   
                    }
                """)

        # If there are no valid cards, return
        if total_cards == 0:
            main_label.setText("All of your card(s)'s fields are filled!")
            layout.addWidget(main_label)

            action_button = QPushButton("Close")
            action_button.clicked.connect(popup_window.reject)
            layout.addWidget(action_button)

            popup_window.show() 
            return

        # If there is no language specified by the user, return
        if not self.language:
            main_label.setText("Language not specified! Please go to \"Advanced -> Language\" and enter desired language!")
            layout.addWidget(main_label)

            action_button = QPushButton("Close")
            action_button.clicked.connect(popup_window.reject)
            layout.addWidget(action_button)

            popup_window.show() 
            return
        
        main_label.setText("Welcome! Press \"Start\" to Begin!")
        layout.addWidget(main_label)

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

        # Creation of Generate Button
        action_button = QPushButton("Start")
        layout.addWidget(action_button)

        """ Backend Side """
        tries = 0

        # Inserting CSS into each card for highlight words
        custom_css = ".defined-word {}"
        model = mw.col.models.current()
        if "defined-word" not in model["css"]:
            model["css"] += custom_css
            mw.col.models.save(model)
            mw.reset()

        # Function updates the progress bar
        def update_progress_bar():
            nonlocal current_progress
            current_progress += 1
            progress_bar.setValue(current_progress)

            percentage = int(((current_progress) / total_cards) * 100)
            progress_label.setText(f"{percentage}%")

            QApplication.processEvents()

            if current_progress == total_cards:
                action_button.setEnabled(True)
                action_button.setText("Close")
                action_button.clicked.disconnect()
                action_button.clicked.connect(popup_window.reject)
                
                main_label.setText("Generation Complete!")
                print(f"Total time: {time.time() - self.time:.2f} seconds")
        
        # Error detection function
        def error(error_msg: str, i: int):
            nonlocal tries
            if tries == 10 and not self.stop_event.is_set():
                self.stop_event.set()
                progress_bar.setParent(None)
                progress_label.setParent(None)

                main_label.setText(error_msg)

                action_button.setEnabled(True)
                action_button.setText("Close")
                action_button.clicked.disconnect()
                action_button.clicked.connect(popup_window.reject)
            else:
                tries += i
        
        # Starts the thread to generate the sentence
        def run() -> None:
            main_label.setText("Generation in Progress:")
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