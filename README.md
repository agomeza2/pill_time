# pill_time
a discord notification bot with sqlite database registery and web page data visualization with included linux systemd services to be run  

See env-examples.txt to see the structure of the .env file 
in both services you have to change the user 
change line 
User=user_machine
with your actual username
also change the actual folder rute in both services in lines
ExecStart=/usr/bin/python3 folder_rute/task.py
WorkingDirectory=folder_rute

web.py can be seen outside local network with tailscale
