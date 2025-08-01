import tkinter as tk    # imports Tkinter library into my code
import speech_recognition as sr
from tkinter import filedialog
import os
import re
import json

class MedicalVoiceParser:
    def __init__(self, root):
        self.root = root
        self.recognizer = sr.Recognizer()
        self.medicalData = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title("Медицинский голосовой парсер")

        self.speakLabel = tk.Label(master=self.root, text="Говорите..")
        self.speakLabel.grid(column=1, row=1)
        self.speakArea = tk.Text(master=self.root, height=2, width=30)
        self.speakArea.grid(column=2, row=1)
        startListeningButton = tk.Button(master=self.root, text="Начать слушать", command=self.startListening, bg="pink")
        startListeningButton.grid(column=3, row=1)

        self.nameOfPatientLabel = tk.Label(master=self.root, text="ФИО пациента:")
        self.nameOfPatientLabel.grid(column=1, row=2)
        self.nameOfPatientArea = tk.Text(master=self.root, height=1, width=30)
        self.nameOfPatientArea.grid(column=2, row=2)
        self.showNameOfPatientButton = tk.Button(master=window, text='Показать имя', command=self.showNameOfPatient)
        self.showNameOfPatientButton.grid(column=3, row=2)

        self.pressureLabel = tk.Label(master=self.root, text="Давление:")
        self.pressureLabel.grid(column=1, row=3)
        self.pressureArea = tk.Text(master=self.root, height=1, width=30)
        self.pressureArea.grid(column=2, row=3)
        self.showPressureButton = tk.Button(master=window, text='Показать давление', command=self.showPressure)
        self.showPressureButton.grid(column=3, row=3)

        self.pulseLabel = tk.Label(master=self.root, text="Пульс:")
        self.pulseLabel.grid(column=1, row=4)
        self.pulseArea = tk.Text(master=self.root, height=1, width=30)
        self.pulseArea.grid(column=2, row=4)
        self.showPulseButton = tk.Button(master=window, text='Показать пульс', command=self.showPulse)
        self.showPulseButton.grid(column=3, row=4)

        self.saturationLabel = tk.Label(master=self.root, text="SpO2:")
        self.saturationLabel.grid(column=1, row=5)
        self.saturationArea = tk.Text(master=self.root, height=1, width=30)
        self.saturationArea.grid(column=2, row=5)
        self.showPulseButton = tk.Button(master=window, text='Показать сатурацию', command=self.showSaturation)
        self.showPulseButton.grid(column=3, row=5)

        self.selectFolder = tk.Button(master=self.root, text="Выбрать папку для записи отчётов", command=self.selectFolder)
        self.selectFolder.grid(column=1, row=6)
        self.folderArea = tk.Text(master=self.root, height=1, width=60)
        self.folderArea.grid(column=2, row=6)

        self.makeReport = tk.Button(master=self.root, text="Создать отчёт", command=self.makeReport)
        self.makeReport.grid(column=1,row=7)

    def startListening(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio, language="ru-Ru")
            self.speakArea.insert(tk.END, text + ' ')

        except sr.UnknownValueError:
            speechUnrecognizedErrorLabel = tk.Label(master=self.root, text="Речь не распознана", fg="red")
            speechUnrecognizedErrorLabel.grid(column=4, row=1)
            speechUnrecognizedErrorLabel.after(5000, speechUnrecognizedErrorLabel.destroy)
        except sr.RequestError as e:
            serviceErrorLabel = tk.Label(master=self.root, text=f"Ошибка сервиса; {e}", fg="red")
            serviceErrorLabel.grid(column=4, row=1)
            serviceErrorLabel.after(5000, serviceErrorLabel.destroy)

    def showNameOfPatient(self):
        try:
            text = self.speakArea.get('1.0', 'end-1c')
            nameOfPatient = re.search('(?:пациент|больной)\s([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)', text)
            self.nameOfPatientArea.delete('1.0', tk.END)
            self.nameOfPatientArea.insert(tk.END, nameOfPatient.group(1))
            self.recordNameOfPatient(nameOfPatient.group(1))

        except AttributeError:
            nameErrorLabel = tk.Label(master=self.root, text="Скажите ФИО пациента в формате: <пациент> <Фамилия> <Имя> <Отчество>", fg="red")
            nameErrorLabel.grid(column=4, row=2)
            nameErrorLabel.after(5000, nameErrorLabel.destroy)
    
    def recordNameOfPatient(self, name):
        nameOfPatientList = name.split()
        self.medicalData["name"] = {
            'lastName': nameOfPatientList[0],
            'firstName': nameOfPatientList[1],
            'middleName': nameOfPatientList[2],
        }
 
    def showPressure(self):
        try:
            text = self.speakArea.get('1.0', 'end-1c')
            pressure = re.search('(?:давление|АД)\D*(\d{2,3})\s*(?:на|\/)\s*(\d{2,3})', text, re.IGNORECASE)
            self.pressureArea.delete('1.0', tk.END)
            self.pressureArea.insert(tk.END, f"{pressure.group(1)}/{pressure.group(2)}")
            self.recordPressure(pressure.group(1), pressure.group(2))

        except AttributeError:
            pressureErrorLabel = tk.Label(master=self.root, text="Скажите давление пациента в формате: <давление> <Систолическое> на <Диастолическое>", fg="red")
            pressureErrorLabel.grid(column=4, row=3)
            pressureErrorLabel.after(5000, pressureErrorLabel.destroy)
    
    def recordPressure(self, systolicValue, diastolicValue):
        if "hemodynamics" not in self.medicalData:
            self.medicalData["hemodynamics"] = {}

        self.medicalData["hemodynamics"]["blood_pressure"] = {
            "systolic": systolicValue,
            "diastolic": diastolicValue
        }

    def showPulse(self):
        try:
            text = self.speakArea.get('1.0', 'end-1c')
            pulse = re.search('(?:пульс|ЧСС)\D*(\d{2,3})', text, re.IGNORECASE)
            self.pulseArea.delete('1.0', tk.END)
            self.pulseArea.insert(tk.END, pulse.group(1))
            self.recordPulse(pulse.group(1))

        except AttributeError:
            pulseErrorLabel = tk.Label(master=self.root, text="Скажите пульс пациента в формате: <пульс> или <ЧСС> <Значение>", fg="red")
            pulseErrorLabel.grid(column=4, row=4)
            pulseErrorLabel.after(5000, pulseErrorLabel.destroy)
    
    def recordPulse(self, pulseValue):
        if "hemodynamics" not in self.medicalData:
            self.medicalData["hemodynamics"] = {}

        self.medicalData["hemodynamics"]["heart_rate"]= {
            "value": pulseValue
        }

    def showSaturation(self):
        try:
            text = self.speakArea.get('1.0', 'end-1c')
            saturation = re.search('(?:сатурация|SpO2)\D*(\d{1,2})', text, re.IGNORECASE)
            self.saturationArea.delete('1.0', tk.END)
            self.saturationArea.insert(tk.END, saturation.group(1))
            self.recordSaturation(saturation.group(1))

        except AttributeError:
            saturationErrorLabel = tk.Label(master=self.root, text="Скажите SpO2 пациента в формате: <сатурация> или <SpO2> <Значение>", fg="red")
            saturationErrorLabel.grid(column=4, row=5)
            saturationErrorLabel.after(5000, saturationErrorLabel.destroy)
    
    def recordSaturation(self, saturationValue):
        if "hemodynamics" not in self.medicalData:
            self.medicalData["hemodynamics"] = {}

        self.medicalData["hemodynamics"]["saturation"] = {
            "value": saturationValue
        }

    def selectFolder(self):
        sourcePath = filedialog.askdirectory(title='Выберите папку для записи отчётов')
        self.folderArea.insert(tk.END, sourcePath)

    def makeReport(self):
        try:
            if self.folderArea.compare('end-1c', '!=', '1.0'):
                folder = self.folderArea.get('1.0', 'end-1c')
                nameOfReportFile = ' '.join(self.medicalData["name"].values())
                nameOfFile = re.sub('\s', '_', nameOfReportFile.upper())
                pathToFile = folder + '/' + nameOfFile
                self.writeDataToJsonFile(pathToFile)

                typstDocument = f'''#set page(
    paper: "a4",
    margin: 2cm
)

#set text(
    font: ("Times New Roman", "Libertinus Serif"),
    size: 12pt,
)

#align(center)[
    #text(weight: "bold", size: 16pt)[МЕДИЦИНСКОЕ ЗАКЛЮЧЕНИЕ]
    #linebreak()
    #text(style: "italic", size: 10pt)[Дата: #datetime.today().display("[day].[month].[year]")]
]

#let jsonData = json("''' + nameOfFile + '''.json")
#for value in jsonData {
    block(
        fill: rgb("#f0f0f0"),
        inset: 8pt,
        radius: 4pt,
        stroke: (left: 2pt + blue)
    )[
        #if "name" in value {
            if value.name != "" {
                text(weight: "bold")[ПАЦИЕНТ:]
                [ #value.name.lastName #value.name.firstName #value.name.middleName ]
            }
        }
    ] 
    if "hemodynamics" in value {
        if "blood_pressure" in value.hemodynamics {
            if value.hemodynamics.blood_pressure != "" {
                [ *Давление*: #value.hemodynamics.blood_pressure.systolic/#value.hemodynamics.blood_pressure.diastolic мм рт. ст. ]
                linebreak()
            }
        }
        if "heart_rate" in value.hemodynamics {
            if value.hemodynamics.heart_rate != "" {
                [ *Пульс*: #value.hemodynamics.heart_rate.value уд/мин. ]
                linebreak()
            }
        } 
        if "saturation" in value.hemodynamics {
            if value.hemodynamics.saturation != "" {
                [ *SpO2*: #value.hemodynamics.saturation.value% ]
                linebreak()
            }
        } 

        block(
            fill: rgb("#f8f8f8"),
            inset: 12pt,
            radius: 4pt,
            stroke: 0.5pt + black
        )[
            #text(weight: "bold")[ЗАКЛЮЧЕНИЕ:]
            #linebreak()
            На основании проведённого осмотра и показателей гемодинамики:

            #if "blood_pressure" in value.hemodynamics {
                let sys = int(value.hemodynamics.blood_pressure.systolic)
                let dia = int(value.hemodynamics.blood_pressure.diastolic)
                if sys < 90 or dia < 60 {
                    [ - Артериальное давление снижено (гипотензия) ]
                } else if sys > 140 or dia > 100 {
                    [ - Артериальное давление повышено (гипертензия) ]
                } else {
                    [ - Артериальное давление в пределах нормы ]
                }
            } 
            #if "heart_rate" in value.hemodynamics {
                let hr = int(value.hemodynamics.heart_rate.value)
                if hr < 60 {
                    [ - Брахикардия ]
                } else if hr > 100 {
                    [ - Тахикардия ]
                } else {
                    [ - ЧСС в пределах нормы ]
                }
            }
            #if "saturation" in value.hemodynamics {
                let spo2 = int(value.hemodynamics.saturation.value)
                if spo2 < 95 {
                    [ - Сниженная сатурация кислорода ]
                } else {
                    [ - Сатурация кислорода в пределах нормы ]
                }
            }
        ]

        linebreak()
        text(weight: "bold")[РЕКОМЕНДАЦИИ:]
        linebreak()
        list(
            [ Контроль показателей гемодинамики ],
            [ При ухудшении состояния - обратиться к врачу ]
        )
    }

    align(right)[
        #line(length: 6cm)
        #text(style: "italic")[Врач-специалист]
    ]
}'''

                nameOfTypstFile = pathToFile + '.typ'
                with open(nameOfTypstFile, "w", encoding='utf8') as typstFile:
                    typstFile.write(typstDocument)

                nameOfPdfFile = pathToFile + '.pdf'
                os.system('typst compile {reportTYP} {reportPDF}'.format(reportTYP=nameOfTypstFile, reportPDF=nameOfPdfFile))

            else:
                folderErrorLabel = tk.Label(master=self.root, text="Не выбрана папка", fg="red")
                folderErrorLabel.grid(column=2, row=7)
                folderErrorLabel.after(5000, folderErrorLabel.destroy)
    
        except KeyError:
            keyErrorLabel = tk.Label(master=self.root, text="Нет имени пациента", fg="red")
            keyErrorLabel.grid(column=2, row=7)
            keyErrorLabel.after(5000, keyErrorLabel.destroy)
            
    def writeDataToJsonFile(self, nameOfFile):
        nameOfJsonFile = nameOfFile + '.json'
        with open(nameOfJsonFile, "w", encoding='utf8') as jsonFile:
            json.dump([self.medicalData], jsonFile, indent=4, ensure_ascii=False)

window = tk.Tk()    # initializes Tk object called window
app = MedicalVoiceParser(window)
window.mainloop()   # creates the whole window to execute