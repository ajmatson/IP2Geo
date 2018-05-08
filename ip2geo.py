#!/usr/bin/env python

'''
This is a customized script that is designed to pull a real time blacklist feed of IP addresses from
ransomwaretracker.com and compare the IP addresses to a location database provided bytearray ip2location.com.
It then removes entries for countries already blocked by an IPS and alerts on new ones that need to be added 
to manual blacklist on IPS. This was created for a proprietary project but can be customized for use.
 '''

__author__ = "Alan J. Matson"
__license__ = "GPL"
__version__ = "0.91"
__maintainer__ = "Alan J. Matson"
__email__ = "alan.matson@insight.com"
__status__ = "Beta"

countrylist = ['Afghanistan',
'Kazakhstan',
'Kyrgyzstan',
'Moldova',
'Pakistan',
'Romania',
'Russian Federation',
'Rwanda',
'Saudi Arabia',
'Serbia',
'Seychelles',
'Sierra Leone',
'Slovakia',
'Slovenia',
'Somalia',
'Sri Lanka',
'Sudan',
'Svalbard',
'Syria',
'Syrain',
'Tajikistan',
'Tanzania',
'Timor-Leste',
'Togo',
'Tokelau',
'Tunisia',
'Turkey',
'Turkmenistan',
'Turks',
'Uganda',
'Ukraine',
'United Arab Emirates',
'Uzbekistan',
'Yemen',
'Zambia',
'Zimbabwe']

# Import needed modules
import IP2Location, os, urllib, time, smtplib, zipfile, time, hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

date = time.strftime('%m-%d-%Y')
changelog = 'changes_%s.txt' % date


# Generate the MD5 sum of the Blacklist and check if the feed has updated
def genmd5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        data = f.read()
        md5sum = hashlib.md5(data).hexdigest()
    return md5sum
	

# Function to download the updated feed and move current to old
def downloadfeed():
    feed = 'https://ransomwaretracker.abuse.ch/downloads/RW_IPBL.txt'
    urllib.urlretrieve(feed, "tmpfile.txt")
    md5local = genmd5("RW_IPBL-New.txt")
    md5remote = genmd5("tmpfile.txt")
    if md5local!= md5remote:
        if os.path.exists('RW_IPBL-Old.txt'):
            os.remove('RW_IPBL-Old.txt')
        if os.path.exists('RW_IPBL-New.txt'):
            os.rename('RW_IPBL-New.txt','RW_IPBL-Old.txt')
        urllib.urlretrieve (feed, "RW_IPBL-New.txt")
    os.remove('tmpfile.txt')


# Download an updated Geo Database, occurs after 7 days of staleness
def downloaddatabase():
    database = 'http://download.ip2location.com/lite/IP2LOCATION-LITE-DB1.BIN.ZIP'
    if os.path.exists('IP2LOCATION-LITE-DB1.BIN.backup'):
        os.remove('IP2LOCATION-LITE-DB1.BIN.backup')
    if os.path.exists("IP2LOCATION-LITE-DB1.BIN"):
        os.rename('IP2LOCATION-LITE-DB1.BIN','IP2LOCATION-LITE-DB1.BIN.backup')
    urllib.urlretrieve (database, "IP2LOCATION-LITE-DB1.BIN.ZIP")
    with zipfile.ZipFile('IP2LOCATION-LITE-DB1.BIN.zip', 'r') as z:
        z.extractall('C:\\Users\\user01\\Desktop\\Scripts\\')


# Run the Geo-Location match for each IP address
def geocheck(address):
    iptocheck = address.strip()
    IP2LocObj = IP2Location.IP2Location();
    IP2LocObj.open("IP2LOCATION-LITE-DB1.BIN");
    rec = IP2LocObj.get_all(iptocheck);
    country = rec.country_long
    return country


# Check for removal of IPs
def removalcheck():
    sourcef = 'RW_IPBL-New.txt'
    destf = 'RW_IPBL-Old.txt'
    changef = open(changelog, 'w')
    changef.write("### Added IP Addresses ###\n")
    for x in open(sourcef):
        if not x.startswith('#'):
            if not x in open(destf):
                ccode = geocheck(x)
                ccode = ccode.strip()
                ipaddy = x.strip()
                if ccode not in countrylist:
                    print "+%s    \t%s\n" % (ipaddy, ccode)
                    changef.write("+ %s    \t%s\n" % (ipaddy, ccode))
    changef.write("\n\n### Removed IP Addresses ###\n")
    for y in open(destf):
        if not y.startswith('#'):
            if not y in open(sourcef):
                print "-%s" % y
                changef.write("- %s" % y)
    changef.close()


# Send the alert email if enabled
def sendmail():
    sender = 'ajmatson@ajmatson.com'
    receivers = ['alan.matson@hhsc.state.tx.us', 'ajmatson@gmail.com']
    with open (changelog, 'r') as mydata:
        messageattach = mydata.read()
    ehlo_string = "ajmatson.com"
    message = MIMEMultipart('alternative')
    message['To'] = ", ".join(receivers)
    message['From'] = sender
    message['Subject'] = "Updated Ransomware Tracker Blacklist"
    text = messageattach
    part1 = MIMEText(text, 'plain')
    message.attach(part1)
    smtpObj = smtplib.SMTP('mail.ajmatson.com', 25)
    smtpObj.ehlo(ehlo_string)
    smtpObj.sendmail(sender, receivers, message.as_string())
    smtpObj.quit()


def main():
    downloadfeed()
    dbtime = os.path.getmtime('C:\\Users\\user01\\Desktop\\Scripts\\IP2LOCATION-LITE-DB1.BIN')
    currtime = int(time.time())
    timediff = currtime - dbtime
    if timediff > 604800:
        downloaddatabase()
    removalcheck()
    #sendmail()

if __name__ == "__main__":
    main()
