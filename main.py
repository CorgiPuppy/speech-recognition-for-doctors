import tkinter as tk    # imports Tkinter library into my code
import speech_recognition as sr

window = tk.Tk()    # initializes Tk object called window
window.title("My App for doctors")  # sets a title for the window
window.geometry("600x600")  # sets the width and height of the window

recognizer = sr.Recognizer()
microphone = sr.Microphone()

label = tk.Label(master=window, text="Say patient's name..")
label.grid(column=1, row=1)

textArea = tk.Text(master=window, height=1, width=30)
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
        label.grid(column=3, row=1)
    except sr.RequestError as e:
        label = tk.Label(master=window, text=f"Ошибка сервиса; {e}")
        label.grid(column=3, row=1)

button = tk.Button(master=window, text="Начать слушать", command=startListening, bg="pink")
button.grid(column=4, row=1)

window.mainloop()   # creates the whole window to execute