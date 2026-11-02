<div style="display: inline-flex; align-items: center; gap: 10px;" flex-wrap: nowrap;>
    <img width="128" height="128" alt="HAM Logger for Linux - Linuxlog" style="width: 50px; height: 50px;" src="https://github.com/user-attachments/assets/90b187bd-56d7-4d26-b582-de6515c81ed0" />
    <h1 style="margin: 0; font-size: 24px;">LinuxLog  - ham logger for amateur radio station</h1>
</div>
<p>This is a ham logger for the "lazy" amateur radio operator. It allows you to keep a log for everyday radio communications.</p>
<p>This logbook is also for radio amateurs who use the Linux operating system and need a simple, functional logbook.</p>
<p>There are no features for contestmans in this log, as I personally don't participate in contests and don't know exactly what's needed for contests. And so far, no contestmans has been able to clearly describe the specific functionality for contests.</p>
<hr>
<h3>Stack of technologies</h3>
<ul>
<li>Python</li>
<li>Framework PyQt6</li>
<li>MySQL database. This allow using logger by internet (many clients one DB)</li>
<li>API integration with eQSL, QRZ.com, Clublog</li>
<li> Serial port </li>
<li>Runs in a virtual environment to keep your system clean</li>
</ul>
<p><strong>For correct instalation on you Linux - please download archive of code, unzip and run <i>install.sh</i> </strong></p>
<p>Tested in Fedora, Ubuntu, Manjaro </p>
<h3>Functional</h3>
<ul>
  <li><strong>Processing QSO's</strong> add/edit/delete></li>
  <li><strong>eQSL</strong> service. Reciving/sent eQSL in manual mode. Automatic send eQSL after QSO. Image download from eQSL into local FS</li>
  <li><strong>QRZ.com</strong> service. Find image for corespondent. Recieving info about corespondent. Add into qrz.com logbook</li>
  <li><strong>Clublog</strong> service. Reciving/sent QSO in manual mode. Automatic send after QSO</li>
  <li><strong>RIGctl</strong> system. Full control for you transciever by net</li>
  <li><strong>TCI</strong> system. Modern interface for control you transciever</li>
  <li><strong>Telnet cluster</strong> service. Work with telnet clusters (click by spot, console to clusters, spots on panadapter (TCI only))</li>
  <li><strong>Frequency control</strong> frequency control with memory</li>
  <li><strong>Multi window</strong> interface. This allows you to arrange windows as you see fit. It features window coordinate memory, as well as presets that can be saved for different desktop situations.</li>
  <li><strong>Color control</strong> interface. This allows you to adapt Linuxlog to your interface.</li>
</ul>
<p><i>If you have any ideas for this logbook for Linux - please write to bastonsv@gmail.com</i> </p>


<img width="1920" height="1080" alt="Linuxlog - ham radio logger Linux OS" src="https://github.com/user-attachments/assets/e00bc01d-d27b-4ff9-bd1c-e0a8d34d5131" />
<img width="1680" height="1050" alt="Linuxlog - ham radio logger for Ubunt, Fedora, Manjaro" src="https://github.com/user-attachments/assets/19904624-2e91-44fd-a7d6-8e2c89fd4eb5" />
<img width="1680" height="1050" alt="linuxlog3" src="https://github.com/user-attachments/assets/7714fe6a-0ac7-4d42-a32d-bcaabcede2c7" />
<hr>
<p> If you are using a Linux distribution other than Fedora/Ubuntu/Manjaro, install it as follows:
<ol>
    <li>Install the MariaDB database</li>
    <li>Use the virtual environment from the archive <code>source .venv/bin/activate</code></li>
    <li>Install all dependencies <code>pip install -r requirements.txt</code></li>
    <li>Create a .desktop file for the applications menu and copy it to ~/.local/share/applications/</li>
    <li>To connect to the database, enter the appropriate values ​​for your DB server in the settings.cfg file for the db-host, db-user, db-pass, db-name fields.</li>
</ol>

