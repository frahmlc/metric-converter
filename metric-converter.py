# -*- coding: utf-8 -*-

import zipfile
import os
import sys


def convert_units_in_html_file(html_file):
    """
    Detects strings corresponding to numbers in an html file.

    Parameters
    ----------
    html_file: string
        The html file which is examined.

    Returns
    -------

    """
    def split_and_flatten(word_list, separator):
        """ Splits all strings in a list and flattens the list again """
        word_list = [w.split(separator) for w in word_list]
        word_list = [w for l in word_list for w in l]
        return word_list

    units = {'inch': (2.54, 'centimeter'), 'inches': (2.54, 'centimeter'),
             'feet': (0.3048, 'meter'), 'foot': (0.3048, 'meter'),
             'yard': (0.9144, 'meter'), 'yards': (0.9144, 'meter'),
             'mile': (1.60934, 'kilometer'), 'miles': (1.60934, 'kilometer'),
             'pound': (0.4535, 'kilogram'), 'pounds': (0.4535, 'kilogram'),
             'gallon': (3.785, 'liter'), 'gallons': (3.785, 'liters')}

    with open(html_file, 'r') as f:
        content = f.read()

    parts = content.partition('<body>')

    # The third component in this list is the body of the html file
    body = parts[2]

    words = body.split()
    words = split_and_flatten(words, '-')
    words = split_and_flatten(words, '<p>')

    # Find expressions in which the units appear
    expressions = [words[i-4:i+2] for i in range(len(words))
                   if words[i].strip('.,') in units]

    # Find numbers in the expressions and translate into floats
    numbers = [(expression_to_number(expr)) for expr in expressions]

    idx = 0
    # Write the converted units into the body string
    for ind in range(len(expressions)):
        t = numbers[ind]
        expr = expressions[ind]
        idx = body.find(expr[3], idx+1)
        idx = body.find(expr[4], idx)
        split_position = idx + len(expr[4].strip('.,'))
        if t[1]:
            u = units[expr[4].strip('.,')]
            conv_number = t[0]*u[0]
            conv_str = ' (' + '{:.2f}'.format(conv_number) + ' ' + u[1] + ')'
            body = body[:split_position] + conv_str + body[split_position:]

    new_content = parts[0] + parts[1] + body

    with open(html_file, 'w') as f:
        f.write(new_content)


def expression_to_number(expr):
    """
    Converts an expression, which is a list of six strings, with a unit on the
    second to last position, to a number.

    Parameters
    ----------
    expr: list
        The expression, a list of six strings to be converted

    Returns
    -------
    number: float
        The number extracted from the expression

    """

    num_dict = {'Quarter': 0.25, 'Half': 0.5,
                'A': 1, 'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5,
                'Six': 6, 'Seven': 7, 'Eight': 8, 'Nine': 9, 'Ten': 10,
                'Eleven': 11, 'Twelve': 12, 'Dozen': 12, 'Thirteen': 13,
                'Fourteen': 14, 'Fifteen': 15, 'Sixteen': 16, 'Seventeen': 17,
                'Eighteen': 18, 'Nineteen': 19, 'Twenty': 20, 'Thirty': 30,
                'Fourty': 40, 'Fifty': 50, 'Sixty': 60, 'Seventy': 70,
                'Eighty': 80, 'Ninety': 90, 'Hundred': 100, 'Thousand': 1000,
                'Million': 1000000}

    valid = True

    expr = [word.capitalize().strip('.,') for word in expr]

    is_numeric = [word.replace(',', '').replace('.', '').isdigit()
                  for word in expr]
    in_dictionary = [word in num_dict for word in expr]

    if any(is_numeric):
        number = float(expr[is_numeric.index(True)].replace(',', ''))
    elif any(in_dictionary):
        n = [num_dict[w] for w in expr if w in num_dict]
        if expr[-1] in num_dict:
            # special case: if the expr[-1] is in the dictionary, it usually is
            # x foot y
            number = n[0] + n[1] / 12.0
        elif len(n) == 1:
            number = n[0]
        elif len(n) == 2:
            if n[1] < 1:
                number = n[1]
            elif n[0] > n[1]:
                number = sum(n)
            else:
                number = n[0] * n[1]
        elif len(n) > 2:
            if n[2] < 1:
                number = n[0]+n[2]
            else:
                number = 0
                valid = False
    else:
        valid = False
        number = 0

    return number, valid


# Main program

filename = sys.argv[1]

# open the ebook ( a zipfile containing html files )
ebook = zipfile.ZipFile(filename)

namelist = ebook.namelist()
htmllist = [_ for _ in namelist if _.endswith('html')]
ebook.extractall()

# Convert the units for all quantities in the html files
for f in htmllist:
    convert_units_in_html_file(f)

# Edit the content.opf - file
with open('OEBPS/content.opf', 'r') as f:
    content = f.read()

idx = content.find('</dc:title>')

# add ' - converted to metric' to the title of the ebook
content = content[0:idx] + ' - converted to metric' + content[idx:]

with open('OEBPS/content.opf', 'w') as f:
    content = f.write(content)

# now write all the files into a new epub archive and remove them
new_filename = filename.strip('.epub')+'_converted.epub'
with zipfile.ZipFile(new_filename, 'w') as myzip:
    for f in namelist:
        myzip.write(f)
        os.remove(f)

# also remove the directories
dirs = [f.rpartition('/')[0] for f in namelist if '/' in f]
dirs = list(set(dirs))  # remove double entries
dirs.sort(reverse=True)  # sort such that the longest entries come first

for f in dirs:
    os.rmdir(f)
