alias deleteLog='rm ./Desktop/OfficeSensor/sensor.log'
alias showLog='cat ./Desktop/OfficeSensor/sensor.log'
alias autostart='nano /home/pi/.config/autostart/sensor.desktop'
alias reboot='sudo reboot'
alias goto='cd ./Desktop/OfficeSensor'
alias hardReboot='deleteLog; sudo reboot'

alias temp='vcgencmd measure_temp'
alias voltage='vcgencmd measure_volt'
