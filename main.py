import tkinter as tk    # imports Tkinter library into my code
import speech_recognition as sr
import re

window = tk.Tk()    # initializes Tk object called window
window.title("My App for doctors")  # sets a title for the window
window.geometry("600x600")  # sets the width and height of the window

recognizer = sr.Recognizer()
microphone = sr.Microphone()

label = tk.Label(master=window, text="Говорите..")
label.grid(column=1, row=1)

textArea = tk.Text(master=window, height=2, width=30)
textArea.grid(column=2, row=1)

def startListening():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="ru-Ru")
        textArea.insert(tk.END, text)
    except sr.UnknownValueError:
        label = tk.Label(master=window, text="Речь не распознана")
        label.grid(column=4, row=1)
    except sr.RequestError as e:
        label = tk.Label(master=window, text=f"Ошибка сервиса; {e}")
        label.grid(column=4, row=1)

startListeningButton = tk.Button(master=window, text="Начать слушать", command=startListening, bg="pink")
startListeningButton.grid(column=3, row=1)

nameOfPatient = tk.Label(master=window, text="Имя пациента:")
nameOfPatient.grid(column=1, row=2)
resultArea = tk.Text(master=window, height=1, width=30)
resultArea.grid(column=2, row=2)

def showNameOfPatient():
    string = re.search('пациент\s(\w+\s\w+\s\w+)', textArea.get('1.0', 'end-1c'))
    resultArea.insert(tk.END, string.group(1))

showNameOfPatientButton = tk.Button(master=window, text='Показать имя', command=showNameOfPatient)
showNameOfPatientButton.grid(column=3, row=2)

window.mainloop()   # creates the whole window to execute