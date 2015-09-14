
I used the urllib2 python library to read the SEC Filing document
from the defined URL link.  The entire document was read into
a string buffer.  It was cleaned for unnecessary details
(ie: the headers, tailing html markers).  Had to open the page in
the IE in debug mode so I could examine the HTML tags and build the
search strings to grab required data.

The entire script took 15 hrs to write, test, and debug.
The script takes no argument at this time, therefore could
be directly executed as 'python SEC_Filing.py

No additional libraries were used other than 're' 
for regular expressions.  The output of the files are stored in the 
current directory for time being.

Best was done to extract as much info as possible eventhough
source details was not uniform

process:
1. set up a search criteria to grab the <a name>*
2. use re.findall to look for pattern in the buffer (variable link)
3. loop through the tuples in the search buffer
4. further set up new pattern to retrieve details embedded between <div></div>
   tags.  If there were tables, try to gather details from the table
5. make entry in the DOC_LINE_ARRAY for a specific pattern
6. make entry in the PARAGRAPH array for paragraphs that contained '$'
7. after process completion, dump the arrays (DOC_LINE_ARRAY and
   PARAGRAPH_ARRAY) to separate files.