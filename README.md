# Gestione-Palestra
Installation - Linux:

1) sudo apt-get install rabbitmq-server
2) git clone https://github.com/alefranco41/Gestione-Palestra.git
3) cd Gestione-Palestra
4) python3 -m venv <virtual_env_name>
5) source <virtual_env_name>/bin/activate
6) pip install -r requirements.txt
7) cd gestione_palestra
8) bash script.sh


Installation - Windows:

1) Install Erlang/OTP: https://github.com/erlang/otp/releases/download/OTP-27.0/otp_win64_27.0.exe
2) install rabbitmq server: https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.2/rabbitmq-server-3.13.2.exe
3) git clone https://github.com/alefranco41/Gestione-Palestra.git
4) start cmd as administrator
5) cd .\Gestione-Palestra\
6) python -m venv <virtual_env_name>
7) .\<virtual_env_name>\Scripts\activate
8) pip install -r requirements.txt
9) cd gestione_palestra
10) .\script.bat
