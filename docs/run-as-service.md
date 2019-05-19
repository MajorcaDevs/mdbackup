# Automating running of backups

In this section, systemd and cron ways are going to be explained. systemd is the preferred way in case your system has it.

 > It is supposed you already have configured the environment and it works.

For both ways, download the file [automated-script.sh][1] in some place. In this example, the same folder, where the _venv_, configuration and steps are located, is going to be used.

```bash
curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/automated-script.sh > automated-script.sh
chmod +x automated-script.sh
```

## systemd

For systemd, you need to download [backups.service][2] and [backups.timer][3], copy them to `/etc/systemd/system` and enable the timer.

```
sudo bash -c "curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.service > /etc/systemd/system/backups.service"
sudo bash -c "curl -sSL https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.timer > /etc/systemd/system/backups.timer"
sudo nano /etc/systemd/system/backups.service #Modify the path to the script !!
sudo nano /etc/systemd/system/backups.timer #Check when the timer is going to fire !!
sudo systemctl enable backups.timer
sudo systemctl start backups.timer
nano automated-script.sh #Modify the path of CONFIG_FOLDER
```

You **must** modify the path to the script in the `backups.service` and the `CONFIG_FOLDER` in the `automated-script.sh`. It is recommended to check if you like when the timer is going to fire (by default is every night at 1am).

## crontab

For crontab, you need to edit the `root`s crontab and add a new entry. Also modify the `automated-script.sh` file to remove the comment in the last line to have logs visible in the same folder where the configuration and steps are placed. An example of crontab entry could be:

```
0 1 * * * /backups/tool/automated-script.sh
```

[1]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/automated-script.sh
[2]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.service
[3]: https://github.com/MajorcaDevs/mdbackup/raw/master/contrib/backups.timer