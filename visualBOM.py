#!/usr/bin/python3

#---------README---------
#finds given refdes list on schematic pdf file
#adds highlight and annotation with part number and definition
#bom.csv should be in the form as below line
#3xxxx;RES SMD ...;Rxxx
#comma ',' as separator is also OK, this setting may depend on Windows settings
#schematic pdf file name must be input.pdf and BOM file as bom.csv
#emrea, June 2022
#add checking of duplicated parts, Dec 2022
#refactor, Apr 2023

#update this if any change and build new executable with pyinstaller
lastUpdateDate = "Apr 2023"

#references
#https://pymupdf.readthedocs.io/en/latest/tutorial.html
#https://stackoverflow.com/questions/47497309/find-text-position-in-pdf-file/52977595

import fitz #tested with PyMuPDF, 1.19.6
import os
import sys
import time

#input, output files name
inpdf_name = "input.pdf"
outpdf_name = "output.pdf"
bom_name = "bom.csv"
missing_parts = "parts-missing.csv"
duplicate_parts = "parts-duplicated.csv"
dirPath = os.path.dirname(os.path.realpath(__file__))

def annotatePdf():
    texts = []
    text_instances = []
    refdes = [] #parse refdes, later use to check if any duplicate parts in BOM
    f = open(os.path.join(dirPath, bom_name), 'r')
    for line in f.readlines():
        line = line.replace(",", ";") #may depend windows setting, so replace if separator is ","
        l = line.strip().split(';')
        texts.append(l)
    f.close()
    texts_copy = texts.copy() #create a copy of bom list, later used to keep track of missing items in pdf
    #print(texts)
    print("Number of entries for bom list: %s" % len(texts))
    inpdf = os.path.join(dirPath, inpdf_name)
    pdfIn = fitz.open(inpdf)
    print("Number of pages in input pdf: %s" % pdfIn.pageCount)

    print("Start at %s" % time.strftime("%d-%m-%Y-%H:%M:%S"))
    for page in pdfIn:
        print("Processing %s" % page)
        words = page.get_text("words") #get all "words" positions as a list for each page, in this way it can avoid non-exact matches, ie S1 in S14, S15 are avoided
        '''
        https://stackoverflow.com/a/65519008
        output of get_text("words") returns a list of items like this
        (226.74749755859375, 220.7445068359375, 233.947509765625, 229.14450073242188, 'S1', 197, 0, 0)
        (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        x0, y0, ... denotes the rect area where "word" is found
        https://pymupdf.readthedocs.io/en/latest/textpage.html#TextPage.extractWORDS
        '''
        for i in texts:
            if len(i)>1: #may be there are empty lines in bom.csv, which will parsed as [] -empty list-, skip it
                if i[2] != "": #if 3rd element is not empty means there is refdes, search and annotate it
                    refdes.append(i[2]) #this happens page number of times, so one item, appended n times, take care of this
                    for w in words:
                        if w[4] == i[2]: #exact match with pdf texts and search text, this is to prevent non-exact match, ie S1 is in S14, S15 etc
                            inst = fitz.Rect(w[0], w[1], w[2], w[3]) #create Rect like object to annotate
                            #text_instances.append(inst)
                            annot = page.add_highlight_annot(inst)
                            #annot = page.add_rect_annot(inst)
                    
                            #Adding comment to the highlighted text
                            info = annot.info
                            info["title"] = i[0]
                            info["content"] = i[1]
                            annot.set_info(info)
                            #annot.set_popup(annot.rect)
                            #print(annot.rect)
                            annot.update()
                            try:
                                texts_copy.remove(i)
                            except ValueError: #if any items removed for previous pages inspection, this raise ValueError, suppress it
                                pass
        
        #coordinates of each word found in PDF-page
        #print(text_instances)

    #save not founded bom items if any
    if len(texts_copy) > 0: #there are some items, in bom list, those cannot be find in pdf
        f = open(os.path.join(dirPath, missing_parts), 'w')
        print("\nThere are bom items which couldn't be find in pdf file, see %s" % missing_parts)
        print("Reminder, for chassis bom, at least one part should be in %s which is PCB" % missing_parts)
        for i in texts_copy:
            if len(i) > 0: #skip empty lines
                line = ";".join(i)
                f.write("%s\n" % line)
    f.close()
    
    #check duplicate items and save them
    #print(refdes)
    refdesCount = {i:refdes.count(i) for i in refdes}
    #print(refdesCount)
    if sum([*refdesCount.values()]) > len([*refdesCount.values()])*pdfIn.pageCount: #ie [1,1,2,1] sum of values, greater than length, means some values larger than 1
        print("\nThere are duplicate parts in bom, check %s!!!\n" % duplicate_parts)
        f = open(os.path.join(dirPath, duplicate_parts), 'w')
        f.write("refdes;occurrence\n")
        for key, value in refdesCount.items():
            #print(key, value)
            if value > pdfIn.pageCount:
                f.write("%s;%s\n" % (key, round(value/pdfIn.pageCount)))
        f.close()
         
    #Save annotated pdf file
    pdfIn.save(os.path.join(dirPath, outpdf_name))

    print("Finished at %s" % time.strftime("%d-%m-%Y-%H:%M:%S"))
    print("Check %s" % os.path.join(dirPath, outpdf_name))
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        if (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
            print("--------------------")
            print("Place input pdf file to working directory with the name \"%s\"" % inpdf_name)
            print("Place bom list to working directory with the name \"%s\"" % bom_name)
            print("Run executable, it will generate \"%s\" with %s annotated on it" % (outpdf_name, bom_name))
            print("Also \"%s\", \"%s\" if any..." % (missing_parts, duplicate_parts))
            print("Check user manual for further details")
            print("This program is based on PyMuPDF 1.19.6")
            print("There is no guarantee that it works correctly. Use at your own risk!")
            print("EmreA, %s" % lastUpdateDate)
            print("--------------------")
            sys.exit()
        else:
            print("Invalid option, try -h or --help")
            sys.exit()
    
    if not (os.path.exists(os.path.join(dirPath, inpdf_name)) and os.path.exists(os.path.join(dirPath, bom_name))):
        print("Working files are not found!!!!")
        print("Place %s and %s under working directory" % (inpdf_name, bom_name))
        print("Run \"<exe-name> -h\" or \"<exe-name> --help\" to see short help.")
        input("Press any key to close...")
        sys.exit()
        
    annotatePdf()
    input("Press any key to close...")