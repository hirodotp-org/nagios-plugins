==============
Nagios Plugins
==============

This is a collection of nagios checks.

* check_bacula.py
    Check bacula to make sure specific jobs are getting executed succesfully.

==============

Usage: check_bacula.py [options]

Options:
  -h, --help            show this help message and exit
  -m DATABASE           bacula database title (default: 'bacula')
  -s HOSTNAME           database hostname
  -t HOURS              limit check to within last HOURS
  -j JOB                bacula job to check
  -u USERNAME           database user
  -p PASSWORD           database password
  -o PORT               database port

  Generic Options:
    --timeout=50        Exit plugin with unknown status after x seconds
    --threshold=range   Thresholds in standard nagios threshold format
    --th=range          Same as --threshold
    --extra-opts=@file  Read options from an ini file. See
                        http://nagiosplugins.org/extra-opts
    -d, --debug         Print debug info

  Display Options:
    -v, --verbose       Print more verbose info
    --no-perfdata       Dont show any performance data
    --no-longoutput     Hide longoutput from the plugin output (i.e. only
                        display first line of the output)
    --no-summary        Hide summary from plugin output
    --get-metrics       Print all available metrics and exit (can be combined
                        with --verbose)
    --legacy            Deprecated, do not use

==============

Sample check_bacula.py usage to check number of backups over the past 72 hours

  $ ./check_bacula.py -m bacula -u bacula -p bacula -t 72 -j client-backup --th metric=jobs,ok=2..inf,warning=1..2,critical=0..1

