def strip_accents(string):
    import unicodedata
    return unicodedata.normalize('NFKD',
                                unicode(string)).encode('ASCII', 'ignore')
