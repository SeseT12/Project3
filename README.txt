# README

## Execution instructions
The following instructions indicate how to reproduce the simulation that was presented to Professor McGoldrick during the group interview at the end of the project.

As suggested in submission guidelines, we have made a runme.sh file which can be found in the project directory. This runs the following two Python scripts:
- global_node_start.py (Python script for initialising the network)
- keyserver_start.py (script for initialising our keyserver)

During the simulation we presented to the professor, these two scripts were running on two separate RPis to demonstrate connectivity across multiple devices.

The only difference between the code in this directory and the code from the presentation is the hostname at line 25 of Network/node.py (this had to be hardcoded to ensure correct functioning on the RPis).

A few comments relcated to executing the code:

(1) The runme script can be executed by running './runme.sh' from the terminal.You may need to run 'chmod +x runme.sh' before executing this script on your machine.
(2) If you encounter an issue related to too many threads running (typically OSError: [Errno 48] Address already in use), it's likely your machine's limit on the number of concurrent processes is too low.
    We noticed that the number of concurrent processes stabilises in the range of 300 to 500 threads.
    You should therefore increase this limit by running 'ulimit -n 1024'. This change is temporary and specific to the current shell session.
    Please note that this issue is not related to your machine's actual power; the RPi ran this code without needing to modify the thread limit, whereas on a computer with an M2 Pro processor this was necessary.
(3) If you run the runme.sh script (or any of the Python scripts that it contains) multiple times in a short timespan, it is possible you will encounter an issue related to the ports still being occupied.
    You can either wait for the ports to be freed up (as the processes are automatically killed by your machine), or run the cleanup.sh script which kills any processes using the ports used by our project.
    Additionally, we've found that it's still best to wait 10-30 seconds before continuing to guarantee correct network performance.
    See (1) for details on how to run shells scripts and be cautious when using this approach, as it may lead to unexpected behavior, especially if the processes being terminated are critical to your system.
(4) This code ran correctly on both Python 3.8 (on the RPi) and Python 3.11 (on our local machines). If you encounter any issues relating to Python versions, please use one of these two versions.

## Contributions
As per the submission guidelines, we have indicated the main contributor(s) to the various parts of the codebase.
We have chosen to do this on a per-file basis, as this granularity best captures the effort from various team members towards the final product.
This can on the first line of every file. The contributor(s) is referred to by their TCD shortname, which is as follows for the team:

- Muhammad Omar Alam <alammu>
- Conn Breathnach <cobreath>
- Romain Montange <montangr>
- Sebastian Regitz <regitzs>

The order of shortnames on files with multiple contributors is arbitrary and all contributors can be assumed to have considered equally to every file they are associated with.
