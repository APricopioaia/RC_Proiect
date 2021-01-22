from tkinter import *

fereastra = Tk()

fereastra.title("Client DHCP")
fereastra.geometry("800x500")
fereastra.grid_columnconfigure(0, weight=1)
fereastra.grid_rowconfigure(13, weight=1)

variabile = [BooleanVar() for _ in range(10)]
check_name = ["Optiunea 1", "Optiunea 2", "Optiunea 3", "Optiunea 4", "Optiunea 12", "Optiunea 15", "Optiunea 50", "Optiunea 51", "Optiunea 58", "Optiunea 59" ]

def click():
    vector = [variabile[index].get() for index in range(0,len(variabile))]
    iesire.insert(END, str(vector) + '\n')

for index in range(len(variabile)):
    c = Checkbutton(fereastra, text=check_name[index], variable=variabile[index])
    c.grid(row=index, column=0, sticky=W)

frame = Frame(fereastra)
frame.grid(row=13, sticky='nsew', pady=10)

Button(frame, text='Start', width=8, command=click).pack()
Label(frame, text='TERMINAL:', fg='black').pack()
scrollbar = Scrollbar(frame)
iesire = Text(frame, wrap=WORD, yscrollcommand=scrollbar.set, height=6)

scrollbar.pack(side=RIGHT, fill=Y)
scrollbar.config(command=iesire.yview)
iesire.pack(side=LEFT, expand=True, fill=BOTH)
iesire.bind('<Key>', lambda e: "break")

mainloop()
