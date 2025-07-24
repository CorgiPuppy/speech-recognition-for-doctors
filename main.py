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

        self.label = tk.Label(master=self.root, text="Говорите..")
        self.label.grid(column=1, row=1)

        self.textArea = tk.Text(master=self.root, height=2, width=30)
        self.textArea.grid(column=2, row=1)

        startListeningButton = tk.Button(master=self.root, text="Начать слушать", command=self.startListening, bg="pink")
        startListeningButton.grid(column=3, row=1)

        self.nameOfPatient = tk.Label(master=self.root, text="ФИО пациента:")
        self.nameOfPatient.grid(column=1, row=2)
        self.resultArea = tk.Text(master=self.root, height=1, width=30)
        self.resultArea.grid(column=2, row=2)

        self.showNameOfPatientButton = tk.Button(master=window, text='Показать имя', command=self.showNameOfPatient)
        self.showNameOfPatientButton.grid(column=3, row=2)

        self.selectFolder = tk.Button(master=self.root, text="Выбрать папку для записи отчётов", command=self.createFolder)
        self.selectFolder.grid(column=1, row=3)

        self.makeReport = tk.Button(master=self.root, text="Создать отчёт", command=self.makeReport)
        self.makeReport.grid(column=1,row=4)

    def startListening(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio, language="ru-Ru")
            self.textArea.insert(tk.END, text)
        except sr.UnknownValueError:
            errorLabel = tk.Label(master=self.root, text="Речь не распознана")
            errorLabel.grid(column=4, row=1)
            errorLabel.after(5000, errorLabel.destroy)
        except sr.RequestError as e:
            errorLabel = tk.Label(master=self.root, text=f"Ошибка сервиса; {e}")
            errorLabel.grid(column=4, row=1)
            errorLabel.after(5000, errorLabel.destroy)

    def showNameOfPatient(self):
        try:
            text = self.textArea.get('1.0', 'end-1c')
            nameOfPatient = re.search('(?:пациент|больной)\s([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)', text)
            self.resultArea.delete('1.0', tk.END)
            self.resultArea.insert(tk.END, nameOfPatient.group(1))
            self.recordNameOfPatient(nameOfPatient.group(1))

        except AttributeError:
            errorLabel = tk.Label(master=self.root, text="Скажите ФИО пациента в формате: <пациент> <Фамилия> <Имя> <Отчество>")
            errorLabel.grid(column=4, row=2)
            errorLabel.after(5000, errorLabel.destroy)
    
    def recordNameOfPatient(self, name):
        nameOfPatientList = name.split()
        self.medicalData["name"] = {
            'lastName': nameOfPatientList[0],
            'firstName': nameOfPatientList[1],
            'middleName': nameOfPatientList[2],
        }
 
    def createFolder(self):
        soursePath = filedialog.askdirectory(title='Выберите папку для записи отчётов')
        path = os.path.join(soursePath, 'Отчёты')
        os.makedirs(path)   

    def makeReport(self):
        nameOfReportFile = ' '.join(self.medicalData["name"].values())
        nameOfFile = re.sub('\s', '_', nameOfReportFile.upper())
        self.writeDataToJsonFile(nameOfFile)

        typstDocument = f'''#set text(
    font: "Times New Roman"
)

#let jsonData = json("''' + nameOfFile + '''.json")
#for value in jsonData {
    if value.name != "" {
        [ *Имя пациента*: #value.name.lastName #value.name.firstName #value.name.middleName ]
    }
}
'''

        nameOfTypstFile = nameOfFile + '.typ'
        with open(nameOfTypstFile, "w", encoding='utf8') as typstFile:
            typstFile.write(typstDocument)

        nameOfPdfFile = nameOfFile + '.pdf'
        os.system('typst compile {reportTYP} {reportPDF}'.format(reportTYP=nameOfTypstFile, reportPDF=nameOfPdfFile))

    def writeDataToJsonFile(self, nameOfFile):
        nameOfJsonFile = nameOfFile + '.json'
        with open(nameOfJsonFile, "w", encoding='utf8') as jsonFile:
            json.dump([{k: self.medicalData[k]} for k in self.medicalData], jsonFile, indent=4, ensure_ascii=False)


window = tk.Tk()    # initializes Tk object called window
app = MedicalVoiceParser(window)
window.mainloop()   # creates the whole window to execute