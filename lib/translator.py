#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json

global_lang = "cs_cz"

filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'translations.json')

with open(filename) as f:
    data = f.read()

strings = json.loads(data)

def setLang(lang):
    global global_lang
    global_lang = lang.lower()

def _(text):
    if text in strings and global_lang in strings[text]:
        return strings[text][global_lang]
    return text
