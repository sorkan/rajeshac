import os
import sys
import re
import urllib2


DOC_LINES_ARRAY=[]
PARAGRAPH_ARRAY=[]
tables_hash={}
tables_index=1
STD_CHARS_PERLINE=80
PARAGRAPH_COUNTER=1


def processhtml_remcodechars(html_string):
    
    unicode_srch='&#(.*?);'
    unicode_list=re.findall(unicode_srch, html_string)

    # loop through and replace all occurance of &#dddd
    for unicode_char in unicode_list:
        repsrch='&#%s;' %unicode_char
        html_string=re.sub(repsrch,  '',  html_string)
    # end loop
    return(html_string)
# end function


def processhtml_table(html_string):

    # find 
    try:
      index=html_string.index('</div><div style=')
      temp_str=html_string.replace('</div><div style=',
                                   '</div></td><td style=""><div style=')
      html_string=temp_str
    except ValueError:
      pass

    tab_row_srch='<tr>(.*?)<\/tr>'
    tab_rows=re.findall(tab_row_srch, html_string)

    # process the rows of the table
    TABLE_ROW=[]
    for rows in tab_rows:
      TABLE_COL=[]

      if '<td style=' in rows:
         # process the row if td element has style decl
         tab_col_srch='<td style=(.*?)><div style=(.*?)>'
         tab_col_srch+='<font (.*?)>(.*?)<\/font><\/div><\/td>'
         tab_cols=re.findall(tab_col_srch, rows)

         for cols in tab_cols:
           (td, div, fnt, tab_data) = cols
           if td == '""':
              TABLE_COL[len(TABLE_COL)-1]+=" " + tab_data
           else:
              TABLE_COL.append(tab_data)
         TABLE_ROW.append(TABLE_COL)
      # end condition
    # end loop for row        

    # create printable table
    TAB_STRING=''
    for row in TABLE_ROW:
      for col in row:
        TAB_STRING += '%s\t\t' %col
      TAB_STRING += '\n'

    return(TAB_STRING)
# end function


def preprocess_tabletags(html_string):
    global tables_hash
    global tables_index

    tblsrch='<div style="padding-left(.*?)><table (.*?)>(.*?)'
    tblsrch+='<\/table><\/div><\/div>'
    tbl_match=re.findall(tblsrch, html_string)


    for tbls in tbl_match:
      (div_frmt, tbl_frmt, tbl_detl)=tbls
      table_key='SEC_TBL_%03d' %tables_index
      tables_hash[table_key]=tbl_detl

      # replace block of code containing table
      repsrch_str='<div style="padding-left%s><table %s>' %(div_frmt,tbl_frmt)
      repsrch_str+='%s</table></div></div>' %(tbl_detl)
      replacement='<font style="">HASHTABLE:%s</font></div>'%table_key
      try:
         html_string=re.sub(repsrch_str, replacement, html_string)
      except:
         pass
      tables_index+=1
    #end loop

    return(html_string)
# end function


def word_wrap(string, width=80, ind1=0, ind2=0, prefix=''):
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
    """
    string = prefix + ind1 * " " + string
    newstring = ""
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        try:
          while not string[marker].isspace():
            marker = marker - 1
        except IndexError:
            marker=1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + "\n"
        newstring = newstring + newline
        string = prefix + ind2 * " " + string[marker + 1:]

    return newstring + string
# end function

def SEC_file_writer(filename, info_table):
    outfh=open(filename, 'w')

    for elements in info_table:
      outfh.write('%s' %elements)
    
    outfh.close()
# end function


# Read security Filing detail from: http://goo.gl/UL5o31
SECURL='http://goo.gl/UL5o31'
try:
   req = urllib2.Request('%s' %SECURL)
   req.add_header('User-Agent','Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10')
   response = urllib2.urlopen(req)
   link=response.read()
except:
   print "Error opening URL: %s" %SECURL

#print link
#print "Length of Link: ",len(link)

# remove trailink html info
link=re.sub(r'\t<\/body>\n<\/html>\n<\/TEXT>\n<\/DOCUMENT>\n$', '', link)

# get blocks of pattern matching <a name=(.*?)></a><div>(.*?)<hr *>' and
# create an array of tuple of two items) for further parsing during step thru
regstring='<a name=(.*?)><\/a><div>(.*?)<hr style="page-break-after:always">'
matched_array=re.findall(regstring, link)

# process the matched array
for matched_items in matched_array:
   tables_hash={}  # reset tables
   tables_index=1
   (url, html_code) = matched_items
   if len(url) > 40:
      # some malformed url
      stuff=url[url.index('<div style'):]
      html_code=stuff+html_code
   else:
      print "Processing tag: ",url

   # replace the unicode characters present in the current paragraph
   html_code=processhtml_remcodechars(html_code)

   # search for special table tagging
   if '<table ' in html_code:
      html_code=preprocess_tabletags(html_code)

   html_code = re.sub('</div><br>', '', html_code)
   html_code = re.sub('</font><div></div>', '</font></div>', html_code)
   regstring='<div style=(.*?)><font style=(.*?)>(.*?)<\/font><\/div>'
   sub_matcharay=re.findall(regstring, html_code)

   # process sub_lines for the page
   for sub_html_tuple in sub_matcharay:
      (div_tag, font_tag, sub_html)=sub_html_tuple
      #print(div_tag, font_tag, sub_html)

      if '<br>' in sub_html:
         DOC_LINES_ARRAY.append('\n')
         continue
      
      elif 'HASHTABLE:SEC_TBL' in sub_html:
         try:
            (junk,hashkey)=sub_html.split(':')
            table_html =tables_hash[hashkey]
         except:
            table_html=''
            pass

         table_norm=processhtml_table(table_html)
         DOC_LINES_ARRAY.append(table_norm)
         continue

      #elif '<table ' in div_tag:
      #   DOC_LINES_ARRAY.append('-'*(STD_CHARS_PERLINE+10) + '\n')
      #   continue
      elif 'text-align:center' in div_tag:
         if '</font><font style=' in sub_html:
            sub_html=re.sub(r'</font><font style=.*>', '', sub_html)
         DOC_LINES_ARRAY.append(sub_html.center(STD_CHARS_PERLINE) + '\n')
         continue
      elif 'text-indent' in div_tag:
         PARAGRAPH_COUNTER+=1
         if 'Wingdings' in sub_html:
            sub_html=re.sub(r'<\/font><font style=.*>', '[ ]\t', sub_html)

         #sub_html=word_wrap(sub_html)
         DOC_LINES_ARRAY.append('\t' + sub_html + '\n')
         if '$' in sub_html:
            PARAGRAPH_ARRAY.append("%05d. %s\n" %(PARAGRAPH_COUNTER,sub_html))
         continue
   # end loop - process sublines:

# write to file
print
print "Writing files..."
SEC_file_writer('document.txt', DOC_LINES_ARRAY)

SEC_file_writer('paragraph.txt', PARAGRAPH_ARRAY)   
   
   
sys.exit()

