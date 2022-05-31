#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 27 09:30:22 2022

@author: alexstewart
"""

from urllib.request import urlopen
import json
import pandas as pd
import os
#journal url and journal name

def fetch_new_titles():
    url = "https://www.jstor.org/kbart/collections/all-archive-titles?contentType=journals"

    with urlopen(url) as response:
        body = response.read()

    character_set = response.headers.get_content_charset()
    new_data = body.decode(character_set)
    with open("data.txt", encoding="utf-8", mode="w") as file:
        file.write(new_data)
        
    df = pd.read_csv("data.txt", sep="\t")
    os.remove("data.txt")
    return df
   
def clean_data():
    
    full_title_list_history = fetch_new_titles()

    title_url = full_title_list_history[['publication_title','title_url']]

    return title_url

title_url = clean_data()
