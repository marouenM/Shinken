#!/usr/bin/env python
#
#   Autors: Marouen Morchedi <marouen.morchedi@mhcomm.com>,
#
#   Date: 2012-11
#
# Requires: Python >= 2.7 or Python plus argparse
# Platform: Linux
#

import argparse
import logging
import subprocess
import socket
import errno
import sys
import smtplib
import os
import re

from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
from email.MIMEText import MIMEText
from email.mime.text import MIMEText

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
SMTPserver = 'smtp.gmail.com' # used on get_mail_info
sender =     'morchedi.marouen@gmail.com' # used on get_mail_info
destination = ['mhcommDepo@yopmail.com'] # used on get_mail_info
USERNAME = "morchedi.marouen" # used on get_mail_info actually it is marouen's mail adress
PASSWORD = "09156943" # used on get_mail_info actually it is marouen's mail adress password
text_subtype = 'plain'
content="""\
Test message
"""
subject="Sent from Python" # used on get_mail_info , object of the sended mail
OK_FLAG = 0
WARNING_FLAG = 1
CRITICAL_FLAG = 2
UNKNOWN_FLAG = 3





def mk_parser():
    parser = argparse.ArgumentParser(description='for monitorig (output shinken formated).')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r','--ram', action='store_true', help='get ram info') # argument for supervising memory usage
    group.add_argument('-m','--mail', action='store_true', help='get mail info') # argument for supervising sending mail
    group.add_argument('-d','--disk', action='store_true', help='check free disk space')
    group.add_argument('--tempCPU', action='store_true', help='get mail info') # argument for supervising cpu's temperature 
    group.add_argument('-u','--uwsgi', action='store_true', help='get uwsgi info')
    group.add_argument('-i','--inode', action='store_true', help='get inode info')
    group.add_argument('-p','--pid', action='store_true', help ='get pid info')
	
    parser.add_argument('var1', type=str, nargs='?',help='an integer for compute', default=0)
    parser.add_argument('var2', type=str, nargs='?',help='an integer for compute', default=0) 
    parser.add_argument('var3', type=str, nargs='?',help='an integer for compute', default=0)

    args = parser.parse_args()
    args = parser.parse_args()

    return parser



def get_ram_info(warning, critical):
    proc = subprocess.Popen(['free', '-m'], stdout=subprocess.PIPE) # executing the comand free -m
    info = proc.stdout
    RAM_INFO_LINE = ''
    # travelling the output(info) ligne per ligne and we put each line  on the variable ligne 
    for line in info.xreadlines():
        if line.startswith('-/+ buffers/cache:'):
            RAM_INFO_LINE = line

    RAM_INFO = RAM_INFO_LINE.split()[2:]
    ram_used_average = float(RAM_INFO[0])/(float(RAM_INFO[1])+float(RAM_INFO[0]))*100 # computing the memory used
    
    if ram_used_average > critical: # if the memory used is above the critical threshold 
        ret = CRITICAL_FLAG
	ram_percent = (ram_used_average/critical) *100
        print ('Used Ram CRITICAL : ram used=%s ,max ram=%s ,Ram usage=%s%% | ram_used=%s'% (str(ram_used_average), str(critical), str(ram_percent), str(ram_percent/10)))    

    elif ram_used_average > warning: # if the memory used is above the critical threshold 
        ret = WARNING_FLAG
	ram_percent = (ram_used_average/critical) *100
        print ('Used Ram WARNING : ram used=%s ,max ram=%s ,Ram usage=%s%% | ram_used=%s'% (str(ram_used_average), str(critical), str(ram_percent), str(ram_percent/10)))    
   
    else:
        ret = OK_FLAG # if memory used is below the warning threshold
	ram_percent = (ram_used_average/critical) *100   
        print ('Used Ram  OK : ram used=%s ,max ram=%s ,Ram usage=%s%% | ram_used=%s'% (str(ram_used_average), str(critical), str(ram_percent), str(ram_percent/10)))    
          
    raise SystemExit(ret)



def get_mail_info():
    try:
    	msg = MIMEText(content, text_subtype)
    	msg['Subject']=       subject
    	msg['From']   = sender 

    	conn = SMTP(SMTPserver)
    	conn.set_debuglevel(False)
    	conn.login(USERNAME, PASSWORD)
    	try:
        	conn.sendmail(sender, destination, msg.as_string()) # sending an email from sender to destination having msg.as_string() as message
    	finally:
        	conn.close() # closing the connection
		ret = OK_FLAG
		print ("sending mail OK | mail=%s "% str(1-ret))
		raise SystemExit(ret)

    except Exception, exc:
	ret = CRITICAL_FLAG # if sending mail failed
    	print ( "sending mail CRITICAL; %s | mail=%s" % (str(exc),str(1-ret) )) # give an error message
    	raise SystemExit(ret)




def get_temp_info(temp):
    proc = subprocess.Popen(['sensors'], stdout=subprocess.PIPE) # executing the comand sensors : requires the installation of im-sensors module
    info = proc.stdout
    TEMP_INFO_LINE = ''
    ret = OK_FLAG
    counter=0 # counter used to count lignes on the output

    for line in info.xreadlines(): # travelling the output(info) ligne per ligne and we put each line  on the variable ligne  
        if line.startswith(temp+':'): 

	    

            	TEMP_INFO_LINE = line
	    	TEMP_INFO = TEMP_INFO_LINE.split()[1:]
            	temp = TEMP_INFO[0]
	    	TEMP_CRITICAL = TEMP_INFO[3]
	    	TEMP_WARNING = TEMP_INFO[6]
	    	temperature = float(temp[1:5])
	    	temp_critique = float(TEMP_CRITICAL[1:-5])
	    	temp_warning = float(TEMP_WARNING[1:-5]) 

	    	if(temperature>temp_critique): # if temperature of the cpu is above the critical threshold
			ret = CRITICAL_FLAG 
			print ('CRITICAL : temperature =%s ;Critical temp =%s | tempCPU=%s ' % (str(temperature), str(temp_critique), str(temperature/10)))
			raise SystemExit(ret)

	   	elif(temperature>temp_warning): # if temperature of the cpu is above the warning threshold
			ret = WARNING_FLAG
			print ('WARNING : temperature =%s ;Warning temp =%s |tempCPU=%s' % (str(temperature), str(temp_warning), str(temperature/10)))
			raise SystemExit(ret)
	    	else:  # if temperature of the cpu is below the warning threshold
			print ("OK : temperature = %s, warning = %s, critical = %s | tempCPU=%s" % (str(temperature), str(temp_warning), str(temp_critique),str(temperature/10)))
			raise SystemExit(ret)	
	    
    print (" CPU doesn't exist on the supervisd machine")
    ret = UNKNOWN_FLAG
    raise SystemExit(ret) 




def get_space_check_info(partition,warning,critical):
    command = subprocess.Popen("df -m", stdout=subprocess.PIPE,shell=True)
    disk_info = command.stdout.read()
    sys_part_infos = disk_info.split('\n')[1:-1]
    part_info_tab = []
    ret = 0
    avaible_space =0
    occuped_space_average =0
    percent =0
    counter =0
    for part_info in sys_part_infos:
        split_part_info = part_info.split()
        part_name = split_part_info[0]	
	# if line is different from partition
        if part_name == 'none':
            continue
	if part_name != partition :
	    continue
        # if line is about the partition 
	
        avaible_space = avaible_space + int(split_part_info[3])       
        occuped_space_average = occuped_space_average + int(split_part_info[2])
	percent = percent + int(split_part_info[4][:-1])
        counter = counter+1 # counter to check if the partition has been found
    if(counter != 0): # if partition is found
    	percent = percent/counter
    	if avaible_space < critical:
        	ret += CRITICAL_FLAG 
    	elif occuped_space_average > warning:  #check persent of disk occupation
        	ret += WARNING_FLAG    
    	else:
        	ret += OK_FLAG    
            
        	part_info_tab.append(part_name+' '+str(occuped_space_average)+'%')
   
    	if ret == OK_FLAG: 
        	print ('Free Space check - OK : available space =%s, percent =%s%% | disk_free=%s' % (str(avaible_space), str(percent), str(percent/10.00)))
    	elif ret == WARNING_FLAG:    
        	print ('Free Space check - WARNING : available space =%s, percent =%s%% | disk_free=%s' % (str(avaible_space), str(percent), str(percent/10.00)))
    	elif ret >= CRITICAL_FLAG:
        	ret = CRITICAL_FLAG
        	print ('Free Space check - CRITICAL : available space =%s, percent =%s%% | disk_free=%s' % (str(avaible_space), str(percent), str(percent/10.00000)))
   
    else:
	print ("partition not found")
	ret = UNKNOWN_FLAG 
    raise SystemExit(ret) 



def uwsgi_health_check():
    '''check if only one an unique master uwsgi process is running'''
    import psutil
    
    procs = [psutil.Process(pid) for pid in psutil.get_pid_list()]
    nb_uwsgi_proc = 0
    #uwsgi_pids = []
    
    
    for proc in procs:
        if proc.name == 'uwsgi':
            if len(proc.get_children())>0:
                #uwsgi_pids.append(proc)
                nb_uwsgi_proc += 1
    if nb_uwsgi_proc == 1:
        print ('Uwsgi ps state - OK, %s' % str(nb_uwsgi_proc)) 
        ret = OK_FLAG  
    elif nb_uwsgi_proc < 1:
        print ('Uwsgi ps state - Down, %s ' % str(nb_uwsgi_proc)) 
        ret = CRITICAL_FLAG           
    elif nb_uwsgi_proc > 1:
        print ('Uwsgi ps state - Too many process, %s' % str(nb_uwsgi_proc)) 
        ret = WARNING_FLAG
        
    return ret


    
def inode_check(partition,MIN_INODE_THRESHOLD):
    command = subprocess.Popen("df -i", stdout=subprocess.PIPE,shell=True)
    disk_info = command.stdout.read()
    sys_part_infos = disk_info.split('\n')[1:-1]
    inode_info_tab = []
    ret = 0
    
    for part_info in sys_part_infos:
        split_part_info = part_info.split()
        part_name = split_part_info[0]
        if part_name == 'none':
            continue
	if part_name != partition :
	    continue 
        if split_part_info[4] == '-':
           continue    
        inode_use= int(split_part_info[4][:-1])
        
        if 100 - inode_use < 10 :
            ret += CRITICAL_FLAG 
        elif 100 - inode_use < MIN_INODE_THRESHOLD :  #check persent of disk occupation
            ret += WARNING_FLAG    
        else:
            ret += OK_FLAG    
            
        inode_info_tab.append(part_name+' '+str(inode_use)+'%')
   
    
    if ret == OK_FLAG: 
        print ('Used inode check - OK, %s' % str(inode_info_tab)[1:-1])
    elif ret == WARNING_FLAG:    
        print ('Used Space check - WARNING, %s' % str(inode_info_tab)[1:-1])
    elif ret >= CRITICAL_FLAG:
        ret = CRITICAL_FLAG
        print ('Used Space check - CRITICAL, %s' % str(inode_info_tab)[1:-1])
   
   
    return ret

def get_pid_info(warningpercent,criticalpercent):
    ret = 0
    numberofpid =0
    proc = subprocess.Popen(['ps', 'auxh'], stdout=subprocess.PIPE)
    info = proc.stdout
	 
    #Counting the number of process wich are running
    for line in info.xreadlines():
    	numberofpid  = numberofpid +1
 
    #get the maximum number of process from the file /proc/sys/kernel/pid_ma	
    source = open("/proc/sys/kernel/pid_max", "r")
    toutesleslignes = source.readlines() 
    number = toutesleslignes[0]
    percent =((numberofpid)/ int(number))*100
    if percent > criticalpercent:
	print ("process number - Critical, percnet=%%s | percent=%s" % (str(percent),str(percent/10)))
	ret = CRITICAL_FLAG 
    elif percent > warningpercent:   
        print ("process number - Warning, percnet=%%s | percent=%s" % (str(percent),str(percent/10)))
	ret = WARNING_FLAG 
    elif percent < warningpercent:
	print ("process number - OK, percnet=%s%% | percent=%s" % (str(percent),str(percent/10)))
	ret = OK_FLAG 
    else:
	print ("process number - Unknown")
	ret = UNKNOWN_FLAG
	
    return ret	
       

	
def main():
    args = sys.argv[1:]
    parser = mk_parser()
    options = parser.parse_args(args)

    if options.ram:
	if(len(args)>2):
    		get_ram_info(int(sys.argv[2]),int(sys.argv[3])) # sys.argv[2] is the warning value and sys.argv[3] is the critical one
	else:
		print "need more args : warning value , critical value"

    if options.mail:
    	get_mail_info() 

    if options.disk:
	if(len(args)>3):
		get_space_check_info(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
	else:
		print "need more args : warning value , critical value"

    if options.tempCPU:	
	if(len(args)>1):
    		get_temp_info(sys.argv[2]) # sys.argv[2] is the number of the cpu supervised
	else:
		print "need more args : name of the cpu to supervise" 
   
    if options.uwsgi:
	uwsgi_health_check()

    if options.inode:
        if(len(args)>2):   
        	inode_check(sys.argv[2],int(sys.argv[3]))
	else:
		print "need more args : partiton name, minimum inode threshold"
    
    if options.pid:
	if(len(args)>2):
		get_pid_info(int(sys.argv[2]),int(sys.argv[3]))
	else:
		print "need more args : percent"
	

if __name__ == "__main__":
    main()
