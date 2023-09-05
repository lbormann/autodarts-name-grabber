# AUTODARTS-NAME-GRABBER
[![Downloads](https://img.shields.io/github/downloads/lbormann/autodarts-name-grabber/total.svg)](https://github.com/lbormann/autodarts-name-grabber/releases/latest)


Grabs player-names for https://autodarts.io


## INSTALL INSTRUCTION


### Desktop-OS / Headless-OS:

- Download the appropriate executable in the release section.


### By Source:

#### Setup python3

- Download and install python 3.x.x for your specific os.
- Download and install pip.


#### Get the project

    git clone https://github.com/lbormann/autodarts-name-grabber.git

Go to download-directory and type:

    pip3 install -r requirements.txt




## RUN IT

You can run by source or run an os specific executable.


### Run by executable

#### Example: Windows 

Create a shortcut of the executable; right click on the shortcut -> select properties -> add [Arguments](#Arguments) in the target input at the end of the text field.

Example: C:\Downloads\autodarts-name-grabber.exe -U "your-autodarts-email" -P "your-autodarts-password" -TP "absolute-path-to-your-template-files"

Save changes.
Click on the shortcut to start the application.


### Run by source

#### Example: Linux

Copy the default script:

    cp start.sh start-custom.sh

Edit and fill out [Arguments](#Arguments):

    nano start-custom.sh

Make it executable:

    chmod +x start-custom.sh

Start the script:

    ./start-custom.sh



### Arguments

- -U / --autodarts_email
- -P / --autodarts_password
- -TP / --templates_path
- -GI / --grab_interval



*`-U / --autodarts_email`*

You should know your autodarts.io registered email-adress.

*`-P / --autodarts_password`*

You should know your autodarts.io registered password. Make sure you disable 2FA (Two-Factor-Auth).

*`-TP / --templates_path`*

You need to set an absolute path to your template-file-directory. Moreover make sure the given path doesn't reside inside main-directory (autodarts-name-grabber).

*`-GI / --grab_interval`*

Determines how often (in seconds) names will be grabbed. Default is '60'





### Setup autostart [linux] (optional)

There are endless possibilities to manage an autostart. You find two ways to do it (both using the start-custom.sh to run it by source)

#### Using a cronjob

    crontab -e

At the end of the file add (Replace USER):

    @reboot sleep 30 && cd /home/USER/autodarts-name-grabber && ./start-custom.sh > /home/USER/autodarts-name-grabber.log 2>&1

Reboot your system:

    sudo reboot

Check log:

    tail /home/USER/autodarts-name-grabber.log




#### Using a desktop-start-task (linux with gui only)

if you are facing problems with the crontab-solution try this:

    sudo apt install xterm

One can now manually test whether the whole thing starts with the following command (adjust USER):

    xterm -e "cd /home/USER/autodarts-name-grabber && ./start-custom.sh"

A terminal-like window should now open with the running program.

To enable autostart, a .desktop file now needs to be created:

    sudo nano ~/.config/autostart/autodartscaller.desktop

Insert the following into this file and adjust the USER in the path:

    [Desktop Entry]
    Type=Application
    Exec=xterm -e "cd /home/USER/autodarts-name-grabber && ./start-custom.sh > /home/USER/autodarts-name-grabber.log 2>&1"
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    X-GNOME-Autostart-Delay=10
    Name[de_DE]=autodarts-name-grabber
    Name=autodarts-name-grabber
    Comment[de_DE]=Autostart autodarts-name-grabber
    Comment=Autostart autodarts-name-grabber

Afterwards, save the file (Ctrl + O) and close the file (Ctrl + X).

Now the file permissions need to be set for the file (again, adjust USER!):

    sudo chmod u=rw-,g=rw-,o=r-- ~/.config/autostart/autodartscaller.desktop
    sudo chmod +x ~/.config/autostart/autodartscaller.desktop
    sudo chown USER ~/.config/autostart/autodartscaller.desktop

Reboot your system:

    sudo reboot

Check log:

    tail /home/USER/autodarts-name-grabber.log





## BUGS

It may be buggy. I've just coded it for fast fun with https://autodarts.io. You can give me feedback in Discord > wusaaa


## TODOs

### Done

- Init project



## LAST WORDS

Thanks to Timo for awesome https://autodarts.io. It will be huge!

