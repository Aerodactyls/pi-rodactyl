# Pi-rodactyl auto start system
The auto start system begins running pi-rodactyl when the pi boots up, and restarts it if the process exits for any reason (successful return code or failure, or anything else). The auto-start is needed as operators will obviously not be running the program themselves, and the restarting makes sure pi-rodactyl can recover from any fatal errors in the process. 

The auto start system runs pi-rodactyl under the `pi` user, as seen in the `User` property of the service. This prevents it from running under `root`, which could create unforseen bugs as most testing and setup of pi-rodactyl occurs through the `pi` user. 

When pi-rodactyl exits, the auto start system restarts it nearly instantly. If pi-rodactyl has some kind of fault where it exits as soon as it gets ran, the repeated running could cause some unforseen performance issues. 

## Setup 

First, ensure all paths, specifically in the actual command being ran (in `ExecStart`) are correct. Then, drop the service file into the `etc/systemd/system` directory by running `sudo cp pi-rodactyl.service /etc/systemd/service` 

In order to enable the system, first run `sudo systemctl enable pi-rodactyl`, then run `sudo systemctl start pi-rodactyl`

Pi-rodactyl should start up and will now auto-start/restart. 

## Deactivate

If you need to stop pi-rodactyl from restarting, autorunning, and running at all, first run `sudo systemctl disable pi-rodactyl` and then run `sudo systemctl stop pi-rodactyl`

These commands should be run in order, as stopping the system while its still enabled will just cause it to restart and make the stop command do nothing. 