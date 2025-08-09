import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import json
import os
import threading
from vosk import Model, KaldiRecognizer
import pyaudio

class MedicalVoiceParser:
    def __init__(self, root):
        self.root = root
        self.root.title("Медицинский голосовой парсер")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f4f8")

        # Инициализация модели Vosk
        self.model = Model("models/vosk-model-ru-0.42")
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # Список для хранения данных пациентов
        self.patients = []

        # Расширенный словарь для преобразования чисел из слов в цифры
        self.number_map = {
            'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4,
            'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9,
            'десять': 10, 'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13,
            'четырнадцать': 14, 'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17,
            'восемнадцать': 18, 'девятнадцать': 19, 'двадцать': 20,
            'тридцать': 30, 'сорок': 40, 'пятьдесят': 50, 'шестьдесят': 60,
            'семьдесят': 70, 'восемьдесят': 80, 'девяносто': 90, 'сто': 100,
            'сто десять': 110, 'сто двадцать': 120, 'сто тридцать': 130,
            'сто сорок': 140, 'сто пятьдесят': 150, 'сто шестьдесят': 160,
            'сто семьдесят': 170, 'сто восемьдесят': 180, 'сто девяносто': 190,
            'двести': 200, 'двести десять': 210, 'двести двадцать': 220,
            'двести тридцать': 230, 'двести сорок': 240, 'двести пятьдесят': 250
        }

        # Стоп-слова для исключения из ФИО
        self.stop_words = {'делает', 'неосторожные', 'движения', 'есть', 'был', 'или', 'без', 'на', 'в', 'с', 'по', 'пациент', 'больной'}

        self.setupUI()

    def setupUI(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10), background="#f0f4f8")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Поле для отображения распознанного текста
        ttk.Label(main_frame, text="Распознанный текст:").grid(row=0, column=0, sticky="w", pady=5)
        self.speak_area = tk.Text(main_frame, height=5, width=60, font=("Arial", 10))
        self.speak_area.grid(row=0, column=1, columnspan=2, pady=5)

        # Кнопки управления записью
        self.record_button = ttk.Button(main_frame, text="Начать запись", command=self.startListening)
        self.record_button.grid(row=1, column=1, pady=5, sticky="w")
        ttk.Button(main_frame, text="Очистить текст", command=lambda: self.speak_area.delete("1.0", tk.END)).grid(row=1, column=2, pady=5, sticky="w")

        # Поля ввода данных
        ttk.Label(main_frame, text="ФИО пациента:").grid(row=2, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=60)
        self.name_entry.grid(row=2, column=1, columnspan=2, pady=5)
        ttk.Button(main_frame, text="Извлечь ФИО", command=self.extractName).grid(row=2, column=3, pady=5)

        ttk.Label(main_frame, text="Давление (мм рт. ст.):").grid(row=3, column=0, sticky="w", pady=5)
        self.pressure_entry = ttk.Entry(main_frame, width=60)
        self.pressure_entry.grid(row=3, column=1, columnspan=2, pady=5)
        ttk.Button(main_frame, text="Извлечь давление", command=self.extractPressure).grid(row=3, column=3, pady=5)

        ttk.Label(main_frame, text="Пульс (уд/мин):").grid(row=4, column=0, sticky="w", pady=5)
        self.pulse_entry = ttk.Entry(main_frame, width=60)
        self.pulse_entry.grid(row=4, column=1, columnspan=2, pady=5)
        ttk.Button(main_frame, text="Извлечь пульс", command=self.extractPulse).grid(row=4, column=3, pady=5)

        ttk.Label(main_frame, text="SpO2 (%):").grid(row=5, column=0, sticky="w", pady=5)
        self.saturation_entry = ttk.Entry(main_frame, width=60)
        self.saturation_entry.grid(row=5, column=1, columnspan=2, pady=5)
        ttk.Button(main_frame, text="Извлечь сатурацию", command=self.extractSaturation).grid(row=5, column=3, pady=5)

        # Таблица для отображения записей
        ttk.Label(main_frame, text="Список пациентов:").grid(row=6, column=0, sticky="w", pady=5)
        self.tree = ttk.Treeview(main_frame, columns=("ФИО", "Давление", "Пульс", "SpO2"), show="headings", height=8)
        self.tree.heading("ФИО", text="ФИО")
        self.tree.heading("Давление", text="Давление")
        self.tree.heading("Пульс", text="Пульс")
        self.tree.heading("SpO2", text="SpO2")
        self.tree.column("ФИО", width=200)
        self.tree.column("Давление", width=100)
        self.tree.column("Пульс", width=80)
        self.tree.column("SpO2", width=80)
        self.tree.grid(row=6, column=1, columnspan=3, pady=5)

        # Кнопки управления записями
        ttk.Button(main_frame, text="Добавить запись", command=self.addRecord).grid(row=7, column=1, pady=5, sticky="w")
        ttk.Button(main_frame, text="Удалить запись", command=self.deleteRecord).grid(row=7, column=2, pady=5, sticky="w")
        ttk.Button(main_frame, text="Редактировать запись", command=self.editRecord).grid(row=7, column=3, pady=5, sticky="w")

        # Папка для сохранения
        ttk.Label(main_frame, text="Папка для отчётов:").grid(row=8, column=0, sticky="w", pady=5)
        self.folder_entry = ttk.Entry(main_frame, width=60)
        self.folder_entry.grid(row=8, column=1, columnspan=2, pady=5)
        ttk.Button(main_frame, text="Выбрать папку", command=self.selectFolder).grid(row=8, column=3, pady=5)

        # Кнопки сохранения и генерации
        ttk.Button(main_frame, text="Сохранить все в JSON", command=self.saveAllJSON).grid(row=9, column=1, pady=5, sticky="w")
        ttk.Button(main_frame, text="Создать PDF для всех", command=self.createAllPDF).grid(row=9, column=2, pady=5, sticky="w")

        # Статус-бар
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="red")
        self.status_label.grid(row=10, column=0, columnspan=4, pady=5)

    def showStatus(self, message, duration=5000):
        self.status_var.set(message)
        self.root.after(duration, lambda: self.status_var.set(""))

    def startListening(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_button.configure(text="Остановить запись")
            self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
            self.stream.start_stream()
            threading.Thread(target=self.processAudio, daemon=True).start()
        else:
            self.is_recording = False
            self.record_button.configure(text="Начать запись")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

    def processAudio(self):
        full_text = self.speak_area.get("1.0", "end-1c")
        if full_text and not full_text.endswith("\n"):
            full_text += "\n"

        while self.is_recording:
            try:
                data = self.stream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        full_text += text + "\n"
                        self.speak_area.delete("1.0", tk.END)
                        self.speak_area.insert("1.0", full_text)
                        self.speak_area.see(tk.END)
                else:
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "")
                    if partial_text:
                        self.speak_area.delete("1.0", tk.END)
                        self.speak_area.insert("1.0", full_text + partial_text)
                        self.speak_area.see(tk.END)
            except Exception as e:
                self.showStatus(f"Ошибка обработки аудио: {e}")
                break

    def convertWordsToNumbers(self, text):
        words = text.split()
        result = []
        i = 0
        while i < len(words):
            word = words[i]
            if word in self.number_map:
                number = self.number_map[word]
                # Сотни + десятки + единицы (например, "сто пятьдесят шесть")
                if number >= 100 and i + 2 < len(words) and words[i + 1] in self.number_map and words[i + 2] in self.number_map:
                    tens = self.number_map[words[i + 1]]
                    ones = self.number_map[words[i + 2]]
                    if 20 <= tens <= 90 and 1 <= ones <= 9:
                        result.append(str(number + tens + ones))
                        i += 3
                        continue
                # Сотни + единицы (например, "сто шесть")
                if number >= 100 and i + 1 < len(words) and words[i + 1] in self.number_map:
                    ones = self.number_map[words[i + 1]]
                    if 1 <= ones <= 9:
                        result.append(str(number + ones))
                        i += 2
                        continue
                # Сотни + десятки (например, "сто двадцать") или готовое число (например, "сто двадцать")
                if number >= 100 and i + 1 < len(words) and words[i + 1] in self.number_map:
                    tens = self.number_map[words[i + 1]]
                    if 10 <= tens <= 90:
                        result.append(str(number + tens))
                        i += 2
                        continue
                # Десятки + единицы (например, "девяносто девять")
                if 20 <= number <= 90 and i + 1 < len(words) and words[i + 1] in self.number_map:
                    ones = self.number_map[words[i + 1]]
                    if 1 <= ones <= 9:
                        result.append(str(number + ones))
                        i += 2
                        continue
                # Одиночное число (например, "сто", "восемьдесят")
                result.append(str(number))
                i += 1
            else:
                result.append(word)
                i += 1
        return " ".join(result)

    def extractName(self):
        try:
            text = self.speak_area.get("1.0", "end-1c").lower()
            name_pattern = r"(?:пациент|больной)\s+([а-яё]{2,15})\s+([а-яё]{2,15})\s+([а-яё]{2,15})"
            name_matches = list(re.finditer(name_pattern, text))
            if name_matches:
                last_match = name_matches[-1]
                last_name, first_name, middle_name = last_match.groups()
                if (last_name not in self.stop_words and first_name not in self.stop_words and 
                    middle_name not in self.stop_words and 
                    last_name != "пациент" and first_name != "пациент" and middle_name != "пациент"):
                    name = f"{last_name.capitalize()} {first_name.capitalize()} {middle_name.capitalize()}"
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, name)
                    self.showStatus("ФИО успешно извлечено", 3000)
                    return
            self.showStatus("ФИО не распознано. Скажите: пациент <Фамилия> <Имя> <Отчество>", 5000)
        except Exception as e:
            self.showStatus(f"Ошибка извлечения ФИО: {e}", 5000)

    def extractPressure(self):
        try:
            text = self.speak_area.get("1.0", "end-1c").lower()
            text = self.convertWordsToNumbers(text)
            pressure_pattern = r"(?:давление|ад)\s*(\d{2,3})\s*(?:на|\/)\s*(\d{2,3})"
            pressure_match = re.search(pressure_pattern, text)
            if pressure_match:
                sys, dia = int(pressure_match.group(1)), int(pressure_match.group(2))
                if 80 <= sys <= 250 and 40 <= dia <= 150:
                    self.pressure_entry.delete(0, tk.END)
                    self.pressure_entry.insert(0, f"{sys}/{dia}")
                    self.showStatus("Давление успешно извлечено", 3000)
                else:
                    self.showStatus("Давление вне допустимого диапазона (80–250/40–150)", 5000)
            else:
                self.showStatus("Давление не распознано. Скажите: давление <Число> на <Число>", 5000)
        except Exception as e:
            self.showStatus(f"Ошибка извлечения давления: {e}", 5000)

    def extractPulse(self):
        try:
            text = self.speak_area.get("1.0", "end-1c").lower()
            text = self.convertWordsToNumbers(text)
            pulse_pattern = r"(?:пульс|чсс)\s*(\d{2,3})(?:\s*ударов\s*в\s*минуту)?"
            pulse_match = re.search(pulse_pattern, text)
            if pulse_match:
                pulse = int(pulse_match.group(1))
                if 30 <= pulse <= 200:
                    self.pulse_entry.delete(0, tk.END)
                    self.pulse_entry.insert(0, pulse)
                    self.showStatus("Пульс успешно извлечён", 3000)
                else:
                    self.showStatus("Пульс вне допустимого диапазона (30–200)", 5000)
            else:
                self.showStatus("Пульс не распознан. Скажите: пульс <Число> [ударов в минуту]", 5000)
        except Exception as e:
            self.showStatus(f"Ошибка извлечения пульса: {e}", 5000)

    def extractSaturation(self):
        try:
            text = self.speak_area.get("1.0", "end-1c").lower()
            text = self.convertWordsToNumbers(text)
            saturation_pattern = r"(?:сатурация|spo2)\s*(\d{2,3})(?:\s*процентов)?"
            saturation_match = re.search(saturation_pattern, text)
            if saturation_match:
                saturation = int(saturation_match.group(1))
                if 50 <= saturation <= 100:
                    self.saturation_entry.delete(0, tk.END)
                    self.saturation_entry.insert(0, saturation)
                    self.showStatus("Сатурация успешно извлечена", 3000)
                else:
                    self.showStatus("Сатурация вне допустимого диапазона (50–100)", 5000)
            else:
                self.showStatus("Сатурация не распознана. Скажите: сатурация <Число> [процентов]", 5000)
        except Exception as e:
            self.showStatus(f"Ошибка извлечения сатурации: {e}", 5000)

    def addRecord(self):
        name = self.name_entry.get()
        pressure = self.pressure_entry.get()
        pulse = self.pulse_entry.get()
        saturation = self.saturation_entry.get()

        if not all([name, pressure, pulse, saturation]):
            self.showStatus("Заполните все поля перед добавлением записи", 5000)
            return

        name_parts = name.split()
        if len(name_parts) != 3:
            self.showStatus("ФИО должно содержать фамилию, имя и отчество", 5000)
            return

        patient_data = {
            "name": {
                "lastName": name_parts[0],
                "firstName": name_parts[1],
                "middleName": name_parts[2]
            },
            "hemodynamics": {
                "blood_pressure": {
                    "systolic": pressure.split("/")[0],
                    "diastolic": pressure.split("/")[1]
                },
                "heart_rate": {"value": pulse},
                "saturation": {"value": saturation}
            }
        }

        self.patients.append(patient_data)
        self.tree.insert("", tk.END, values=(name, pressure, pulse, saturation))
        self.showStatus("Запись добавлена", 3000)
        self.clearEntries()

    def deleteRecord(self):
        selected = self.tree.selection()
        if not selected:
            self.showStatus("Выберите запись для удаления", 5000)
            return
        for item in selected:
            index = self.tree.index(item)
            self.tree.delete(item)
            del self.patients[index]
        self.showStatus("Запись удалена", 3000)

    def editRecord(self):
        selected = self.tree.selection()
        if not selected:
            self.showStatus("Выберите запись для редактирования", 5000)
            return
        index = self.tree.index(selected[0])
        patient = self.patients[index]
        self.name_entry.delete(0, tk.END)
        self.pressure_entry.delete(0, tk.END)
        self.pulse_entry.delete(0, tk.END)
        self.saturation_entry.delete(0, tk.END)
        name = f"{patient['name']['lastName']} {patient['name']['firstName']} {patient['name']['middleName']}"
        pressure = f"{patient['hemodynamics']['blood_pressure']['systolic']}/{patient['hemodynamics']['blood_pressure']['diastolic']}"
        self.name_entry.insert(0, name)
        self.pressure_entry.insert(0, pressure)
        self.pulse_entry.insert(0, patient['hemodynamics']['heart_rate']['value'])
        self.saturation_entry.insert(0, patient['hemodynamics']['saturation']['value'])
        self.tree.delete(selected[0])
        del self.patients[index]
        self.showStatus("Запись загружена для редактирования. Внесите изменения и добавьте заново.", 5000)

    def clearEntries(self):
        self.name_entry.delete(0, tk.END)
        self.pressure_entry.delete(0, tk.END)
        self.pulse_entry.delete(0, tk.END)
        self.saturation_entry.delete(0, tk.END)

    def selectFolder(self):
        folder = filedialog.askdirectory(title="Выберите папку для отчётов")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.showStatus("Папка выбрана", 3000)

    def saveAllJSON(self):
        if not self.patients:
            self.showStatus("Нет записей для сохранения", 5000)
            return
        folder = self.folder_entry.get()
        if not folder:
            self.showStatus("Выберите папку для сохранения", 5000)
            return
        filename = filedialog.asksaveasfilename(
            initialdir=folder, defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.patients, f, ensure_ascii=False, indent=4)
            self.showStatus("Данные сохранены в JSON", 3000)

    def createAllPDF(self):
        folder = self.folder_entry.get()
        if not folder:
            self.showStatus("Выберите папку для сохранения", 5000)
            return
        if not self.patients:
            self.showStatus("Нет записей для создания отчётов", 5000)
            return

        for patient in self.patients:
            name = f"{patient['name']['lastName']} {patient['name']['firstName']} {patient['name']['middleName']}"
            filename = re.sub(r'\s+', '_', name.upper())
            json_path = os.path.join(folder, f"{filename}.json")
            typst_path = os.path.join(folder, f"{filename}.typ")
            pdf_path = os.path.join(folder, f"{filename}.pdf")

            # Сохранение JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([patient], f, ensure_ascii=False, indent=4)

            # Создание Typst документа
            typst_content = f"""
            #set page(paper: "a4", margin: 2cm)
            #set text(font: ("Times New Roman", "Libertinus Serif"), size: 12pt)
            #set par(leading: 1.5em, justify: true)

            #align(center)[
                #text(weight: "bold", size: 16pt)[МЕДИЦИНСКОЕ ЗАКЛЮЧЕНИЕ]
                #linebreak()
                #text(style: "italic", size: 10pt)[Дата: #datetime.today().display("[day].[month].[year]")]
            ]

            #let jsonData = json("{filename}.json")
            #for value in jsonData [
                #block(fill: rgb("#f0f0f0"), inset: 8pt, radius: 4pt, stroke: (left: 2pt + blue))[
                    #text(weight: "bold")[ПАЦИЕНТ:] #value.name.lastName #value.name.firstName #value.name.middleName
                ]
                #if "hemodynamics" in value [
                    #if "blood_pressure" in value.hemodynamics [
                        *Давление*: #value.hemodynamics.blood_pressure.systolic/#value.hemodynamics.blood_pressure.diastolic мм рт. ст.
                        #linebreak()
                    ]
                    #if "heart_rate" in value.hemodynamics [
                        *Пульс*: #value.hemodynamics.heart_rate.value уд/мин.
                        #linebreak()
                    ]
                    #if "saturation" in value.hemodynamics [
                        *SpO2*: #value.hemodynamics.saturation.value%
                        #linebreak()
                    ]
                    #block(fill: rgb("#f8f8f8"), inset: 12pt, radius: 4pt, stroke: 0.5pt + black)[
                        #text(weight: "bold")[ЗАКЛЮЧЕНИЕ:]
                        #linebreak()
                        На основании проведённого осмотра и показателей гемодинамики:
                        #if "blood_pressure" in value.hemodynamics [
                            #let sys = int(value.hemodynamics.blood_pressure.systolic)
                            #let dia = int(value.hemodynamics.blood_pressure.diastolic)
                            #if sys < 90 or dia < 60 [
                                - Артериальное давление снижено (гипотензия)
                            ] else if sys > 140 or dia > 100 [
                                - Артериальное давление повышено (гипертензия)
                            ] else [
                                - Артериальное давление в пределах нормы
                            ]
                        ]
                        #if "heart_rate" in value.hemodynamics [
                            #let hr = int(value.hemodynamics.heart_rate.value)
                            #if hr < 60 [
                                - Брахикардия
                            ] else if hr > 100 [
                                - Тахикардия
                            ] else [
                                - ЧСС в пределах нормы
                            ]
                        ]
                        #if "saturation" in value.hemodynamics [
                            #let spo2 = int(value.hemodynamics.saturation.value)
                            #if spo2 < 95 [
                                - Сниженная сатурация кислорода
                            ] else [
                                - Сатурация кислорода в пределах нормы
                            ]
                        ]
                    ]
                    #linebreak()
                    #text(weight: "bold")[РЕКОМЕНДАЦИИ:]
                    #linebreak()
                    #list([Контроль показателей гемодинамики], [При ухудшении состояния - обратиться к врачу])
                ]
                #align(right)[
                    #line(length: 6cm)
                    #text(style: "italic")[Врач-специалист]
                ]
            ]
            """
            with open(typst_path, "w", encoding="utf-8") as f:
                f.write(typst_content)
            os.system(f"typst compile {typst_path} {pdf_path}")
            os.remove(typst_path)

            os.remove(json_path)

        self.showStatus("PDF-отчёты созданы для всех пациентов", 3000)

    def __del__(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalVoiceParser(root)
    root.mainloop()