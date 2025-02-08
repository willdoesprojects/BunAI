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

import sys
import os
from aqt import mw
from aqt.qt import (QObject, QRunnable, pyqtSignal)
from anki.notes import Note
import json
import threading
from bs4 import BeautifulSoup

lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from openai import OpenAI

class WorkerSignals(QObject):
    complete_signal = pyqtSignal()
    error_signal = pyqtSignal(str, int)

class SentenceWorker(QRunnable):
    def __init__(self, expression: str, note: Note, api_key: str, diffculty: str, sentence_field: str, translation_field: str, error_flag: threading.Event, language: str) -> None:
        super().__init__()
        self.expression = expression
        self.note = note
        self.api_key = api_key
        self.diffculty = diffculty
        self.signals = WorkerSignals()
        self.sentence_field = sentence_field
        self.translation_field = translation_field
        self.error_flag = error_flag
        self.language = language

    def run(self) -> None:
        if self.error_flag.is_set():
            return
        client = OpenAI(api_key=self.api_key)

        try:
            target_word = BeautifulSoup(self.note[self.expression], "html.parser").get_text()

            response = client.chat.completions.create(
                model = "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a sentence generator that generates {self.language} sentences with English translation. You must provide the word \"{target_word}\" with its' exact associated conjugation, and the exact English word used in the sentence."},
                    {"role": "user", "content": f"Generate a(n) {self.diffculty} level sentence with using the word: \"{target_word}\"."}
                ],
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                            "name": "sentence_generator",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "translated_sentence": {
                                        "type": "string",
                                        "description": f"The generated {self.language} sentence."
                                    },
                                    "english_sentence": {
                                        "type": "string",
                                        "description": f"The translated English sentence corresponding to the {self.language} sentence."
                                    },
                                    "translated_conjugated_word": {
                                        "type": "string",
                                        "description": f"The exact conjugated {self.language} word used in the generated {self.language} sentence."
                                    },
                                    "english_word": {
                                        "type": "string",
                                        "description": "The exact English word used in the translated English sentence."
                                    }
                                },
                                "required": [
                                    "translated_sentence",
                                    "english_sentence",
                                    "translated_conjugated_word",
                                    "english_word"
                                ],
                                "additionalProperties": False
                                },
                            "strict": True
                    },
                },
                temperature = .7,
                max_tokens=100,
            )
            
            # print(response.choices[0].message.content) 
            data = json.loads(response.choices[0].message.content)
            # print(data)
            # print("")
            translated_word = data["translated_conjugated_word"]
            english_word = data["english_word"]


            sentence = data["translated_sentence"].replace(translated_word, "<span style=\"background-color: rgb(255, 255, 0); color: rgb(0, 0, 0);\">" + translated_word +  "</span>", 1)
            translation = data["english_sentence"].replace(english_word, "<span style=\"background-color: rgb(255, 255, 0); color: rgb(0, 0, 0);\">" + english_word +  "</span>", 1)

            self.note[self.sentence_field] = sentence
            self.note[self.translation_field] = translation

            mw.col.update_note(self.note) 

            self.signals.complete_signal.emit()

        except Exception as e:
                index = str(e).find('{') 
                if index == -1:
                   self.signals.error_signal.emit(str(e), 1)
                else: 
                    self.signals.error_signal.emit(json.loads(str(e)[index-1:].replace("'", '"').replace("None", "null"))["error"]["message"], 1)