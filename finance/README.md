# get_invoice_info.py

I use Color-blind friendly colors on the charts because I have friends who I care about.  Please take things like this into account when you code. Please.

This script is used to get invoice information from linode.  It also takes the linode Rise program into account (heh. thats a nerd joke right there...)

## Misc notes

This fits what I need. You may want other stuff in your reports.  Check out the linode API documentation for all the damage\^H\^H\^H\^H\^H\^Hcool things you can do.  Also - make sure you are using a read-only linode API key.  Also - don't store you secrets in your local filesystem.  Please don't make me come over and revoke your sysadmin privileges.

In addition to graphical charts, it will show a report with the following output:

> ----- Account Summary -----
> 
> company: COMPANY, INC
> email: your_email@email.example
> balance: $0.00
> credit used: $21.91
> active_since: 2023-08-17T12:59:10
> Rise Startup Credit
> - expiration: 2024-11-22T03:59:59
> - credit monthly cap: $100.00
> - credit remaining: $478.09
> - credit remaining this month: $78.09
> 
>.--------------------------- 
> 
> ----- Invoice Totals -----
> 
> Last Month Total: $0.04
> Current Month Total: $0.00
> Year to Date Total: $0.09
> 
> .---------------------------

## Prereqs

  - python3 
  - matplotlib

```bash
pip install -r requirements.txt
```

## Execution

You'll probably want to put this into some kind of automated execution thing.  I use cron by using the following script and adding it to my crontab.  
  
Note: Storing crap in environment variables on a local filesystem is bad form.  You probably really want to point to a secrets manager (Hashicorp, AWS, GCP, etc have them)

To execute:

```bash
#!/bin/bash
. ./path/to/env_vars  
$(which python3) $SCRIPT_HOME/linode_finance.py 2>&1 | tee -a $OUTPUT_DIR/logfile.log
```
