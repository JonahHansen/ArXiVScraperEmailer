#Rudementary ArXiV Scraper and Emailer
#Works with the Python 3 installation on MSO servers
#Credit: Jonah Hansen 2021

#Import a bunch of modules. May require local installations...
import urllib
import feedparser
from datetime import datetime,timedelta
from datetime import time as tm
import sys, time
from urllib.error import HTTPError, URLError
import socket
import yagmail
import time
from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()

#How many papers to scrape in one request. Will do multiple requests, so this
#just affects the load on the server.
slice = 50

#Filename to dump output
filename = "scrape.txt"

wait_time = 3 #seconds to wait before next request
timeout = 10 #seconds
max_attempts = 6 #Max attempts before giving up (if server is down etc.)

#Receiver name and email address
name = "Joe Bloggs"
receiver = "joeBloggs@email.com"

#Sending Email SMTP parameters. Not super secure - use a throwaway gmail account.
sender = "sender@gmail.com"
sender_password = "myPassword"

# Search parameters (eg "astro-ph.EP" for planets)
ls_queries = ["astro-ph.EP","astro-ph.IM","astro-ph.SR"]

f = open(filename, 'w')

def print_entry(entry):

    #Format entry in HTML
    print("<hr>",end="",file=f)
    print ('<p><b>Arxiv-id:</b> %s ' % entry.id.split('/abs/')[-1],file=f)
    print ('<b>Published:</b> %s GMT' % datetime.fromisoformat(entry.published[:-1]).ctime(),file=f)
    print ('<b>Updated:</b> %s GMT </p>' % datetime.fromisoformat(entry.updated[:-1]).ctime(),file=f,end="")
    print ("<p><b>Title:</b>: %s </p>" % entry.title.replace("\n"," "),file=f,end="")

    # feedparser v5.0.1 correctly handles multiple authors, print them all
    try:
        print( '<p><b>Authors:</b>  %s </p>' % ', '.join(author.name for author in entry.authors),file=f,end="")
    except AttributeError:
        pass

    # Lets get all the categories
    all_categories = [t['term'] for t in entry.tags]
    print( '<p><b>All Categories:</b> %s' % (', ').join(all_categories),file=f)

    try:
        comment = entry.arxiv_comment.replace("\n"," ")
    except AttributeError:
        comment = 'No comment found'
    print( '<b>Comments:</b> %s</p>' % comment,file=f,end="")
    print( '<p><b>Abstract:</b> %s</p>' %  entry.summary.replace("\n"," "),file=f,end="")

    # get the links to the abs page and pdf for this e-print
    for link in entry.links:
        if link.rel == 'alternate':
            print( '<p><b>Links: </b><a href="%s">Abs page link</a>' % link.href,file=f,end="")
        elif link.title == 'pdf':
            print( ', <a href="%s">Pdf</a></p>' % link.href,file=f,end="")

    # The abstract is in the <summary> element


# Base api query url
base_url = 'http://export.arxiv.org/api/query?';
today = datetime.now()

#Get ~1 week of papers, plus a few days corresponding to the upload delay
#Change the number of days here depending on when you wish to scrape the ArXiV.
#Essentially refers to the earliest DAY of papers that you wish to recieve
start_date = datetime.fromtimestamp(time.mktime(time.gmtime())) - timedelta(weeks=1,days=3)

#Submission deadline of 7pm GMT
start_datetime = datetime.combine(start_date.date(),tm(19,0))


print("<p>Good Morning %s!</p>" % name,file=f,end="")
print("<p>Beginning ArXiV scrape on %s</p>" % str(today)[:-10],file=f,end="")

#Sort between new and updated papers
published_status = ["Newly Published", "Updated Papers"]
sort = ["submittedDate","lastUpdatedDate"]


# Run through each ArXiV categories
for search_query in ls_queries:

    # Run through new and updated papers
    for index in [0,1]:
        print("<hr>",file=f,end="")
        print(f"<h2>{search_query}: {published_status[index]}</h2>",file=f,end="")

        #Start querying until the date is too far back
        start = 0
        end = 0
        while end == 0:
            #play nice
            time.sleep(wait_time)

            query = 'search_query=cat:%s&start=%i&max_results=%i&sortBy=%s&sortOrder=descending' % (search_query, start, slice, sort[index])

            # Perform a GET request using the base_url and query, with timeout catches
            attempt  = 0
            while 1:
                attempt += 1
                try:
                    response = urllib.request.urlopen(base_url+query,timeout=timeout).read()
                except HTTPError as error:
                    raise Exception('Data not retrieved because %s', error)
                except socket.timeout:
                    print(f"Timeout Occurred, attempt number {attempt}")
                    if attempt > max_attempts:
                        raise Exception("Exceeded max attempts on server. No response")
                    time.sleep(wait_time)
                except URLError as error:
                    if isinstance(error.reason, socket.timeout):
                        print(f"Timeout Occurred, attempt number {attempt}")
                        if attempt > max_attempts:
                            raise Exception("Exceeded max attempts on server. No response")
                        time.sleep(wait_time)
                    else:
                        raise Exception('Some other error happened')
                else:
                    print("Successful request")
                    break

            # parse the response using feedparser
            feed = feedparser.parse(response)

            #Check if enties should be added
            for entry in feed.entries:
                #Only entries with the primary category please!
                if entry.arxiv_primary_category["term"]!=search_query:
                    pass
                #If new papers:
                elif index == 0:
                    #Discard republished papers
                    if entry.published != entry.updated:
                        pass
                    #Check if we are too far back in time
                    elif (datetime.fromisoformat(entry.updated[:-1]) - start_datetime).days <  0:
                        end = 1
                        break
                    #Otherwise, print to file
                    else:
                        print_entry(entry)
                #If updated papers
                elif index == 1:
                    #Discard new papers
                    if entry.published == entry.updated:
                        pass
                    #Check if we are too far back in time
                    elif (datetime.fromisoformat(entry.updated[:-1]) - start_datetime).days < 0:
                        end=1
                        break
                    #Otherwise print to file
                    else:
                        print_entry(entry)

            start += slice
        print(f"Completed {search_query}: {published_status[index]}")

f.close()

print("Beginning Sending")

f = open(filename,"r")

subject = "ArXiV Scrape from %s to %s" % (start_date.date().strftime("%d/%m/%y"),(start_date.date()+timedelta(weeks=1)).strftime("%d/%m/%y"))
body = f.read()
f.close()

yagmail.SMTP(sender, sender_password).send(to=receiver,subject=subject,contents=body)
