#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pypdf>=3.0.0",
# ]
# ///
'''
This program parses a PDF contain multiple client's orders and sorts the orders alphabetically within their 10 minute time slot.
A client's order starts as follows:
Shopping List
Client Name: John Doe
Household Size: 3
Visit Date: 11/7/2025, 4:20pm

'''

import sys
import os

import argparse
from datetime import datetime

try:
   from pypdf import PdfReader, PdfWriter
except:
   sys.exit('failed to load pypdf')


def parse_pdf(filename):
   #the client tuple is:
   # print(f'{client_first_pageno},{number_of_pages},{day_of_week},{visit_time_hour},{visit_time_slot},{client_name_str}')

   client_tuple_list = []
   page_content_list = []

   reader = PdfReader(filename)
   number_of_pages = len(reader.pages)
   print(f'Processing {filename} which has {number_of_pages} pages... This could take a few seconds')
   client_first_pageno = 0
   for pageno in range(number_of_pages):
      page = reader.pages[pageno]
      page_content_list.append(page)
      text = page.extract_text() 
      # print(text + '\n')
      next_line_is_client_name = False
      next_line_is_visit_date = False
      lines = text.split("\n")
      for lineno, line in enumerate(lines):
         if next_line_is_client_name:
            next_line_is_client_name = False
            client_name_list = line.split(' ')
            # put first name last
            first = client_name_list.pop(0)
            client_name_list.append(first)
            client_name_str = ' '.join(client_name_list)
         if line.startswith("Client Name:"):
            next_line_is_client_name = True

         if line.startswith("Visit Date:"):
            # format: Visit Date: 11/7/2025, 4:20pm
            visit_datetime_str = line[12:].strip()
            # print(visit_datetime_str)
            visit_date_str = visit_datetime_str.split(',')[0].strip()
            # print(visit_date_str)
            parsed_date = datetime.strptime(visit_date_str, '%m/%d/%Y')
            # day_name_str = parsed_date.strftime('%A')
            day_of_week = parsed_date.weekday()  # Monday is 0 and Sunday is 6

            visit_time_str = visit_datetime_str.split(',')[1].strip()
            # print(visit_time_str)
            visit_time_obj = datetime.strptime(visit_time_str, '%I:%M%p')
            visit_time_hour = visit_time_obj.hour
            visit_time_slot = int(str(visit_time_obj.minute)[0]) # first digit of minute

         if line.startswith("END OF SHOPPING LIST"):
            number_of_pages = pageno - client_first_pageno + 1
            client_tuple=(client_first_pageno,number_of_pages,day_of_week,visit_time_hour,visit_time_slot,client_name_str)
            # print(f'{client_tuple}')
            client_tuple_list.append(client_tuple)
            client_first_pageno = pageno +1
      # if pageno > 31:
      #    break

   return client_tuple_list, page_content_list

def write_pdf(client_tuple_list, page_content_list, filepath):
   writer = PdfWriter()
   for client in client_tuple_list:
      number_of_pages = client[1]
      for i in range(0,number_of_pages):
         page_to_print = client[0] + i
         writer.add_page(page_content_list[page_to_print])           
   out_file = open(filepath,'wb') 
   writer.write(out_file) 
   out_file.close()

def process_file(input_filename, output_filename, output_directory="."):

   if not os.path.isdir(output_directory):
      sys.exit(f"Failure: '{output_directory}' does not exists or is not a directory.")
   output_pdf_path_filename = os.path.join(output_directory, output_filename)

   client_tuple_list, page_content_list = parse_pdf(input_filename)

   if len(client_tuple_list) == 0:
      print("No clients found in {filename}")
      return

   # sort by {day_of_week},{visit_time_hour},{visit_time_slot},{client_name_str} 
   sorted_client_tuple_list = sorted(client_tuple_list, key=lambda tuple: (tuple[2], tuple[3], tuple[4], tuple[5]))

   # for client_tuple in sorted_client_tuple_list:
   #    print(f'{client_tuple}')
   write_pdf(sorted_client_tuple_list, page_content_list, output_pdf_path_filename)


if __name__ == "__main__":

   input_filename = 'pickup-orders.pdf'

   process_file(input_filename, "pickup-sorted.pdf", "/tmp")
