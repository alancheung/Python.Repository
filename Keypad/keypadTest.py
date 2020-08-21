import PySimpleGUI as sg

layout = [[sg.Text('Hello!')]]

window = sg.Window('Keypad', layout, no_titlebar=True, location=(0,0), size=(800, 400), keep_on_top=False).Finalize()
print(window.GetScreenDimensions())