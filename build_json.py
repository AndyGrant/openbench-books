#!/usr/bin/env python3

# Regenerates the OpenBench book configurations in json/ from the .zip files
# in the root directory. Each .zip must contain exactly one .epd or .pgn file.
#
# The sha is computed exactly the way OpenBench does it: the extracted book is
# read in text mode, encoded back to utf-8, and hashed with sha256.

import argparse
import hashlib
import json
import os
import tempfile
import zipfile

SOURCE = 'https://raw.githubusercontent.com/AndyGrant/openbench-books/master/%s'

def book_sha(fname):
    with open(fname) as fin:
        return hashlib.sha256(fin.read().encode('utf-8')).hexdigest()

def process(zipname, jsondir, verbose):

    with zipfile.ZipFile(zipname) as zf:
        books = [x for x in zf.namelist() if x.lower().endswith(('.epd', '.pgn'))]

        if len(books) != 1:
            print ('SKIP %s: expected 1 .epd/.pgn file, found %d' % (zipname, len(books)))
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            sha = book_sha(zf.extract(books[0], path=tmpdir))

    # OpenBench matches the book by the name of the .zip, so the contained
    # file should agree with it. Warn, but still emit the configuration.
    expected = os.path.basename(zipname)[:-len('.zip')]
    if os.path.basename(books[0]) != expected:
        print ('WARN %s: contains %s' % (zipname, books[0]))

    config = { 'sha' : sha, 'source' : SOURCE % (os.path.basename(zipname)) }
    content = '{\n    "sha"     : "%s",\n    "source"  : "%s"\n}\n' % (config['sha'], config['source'])

    jsonname = os.path.join(jsondir, expected + '.json')
    old = open(jsonname).read() if os.path.isfile(jsonname) else None

    with open(jsonname, 'w') as fout:
        fout.write(content)

    if old is None:
        print ('NEW  %s (%s)' % (jsonname, sha))
    elif json.loads(old) != config:
        print ('EDIT %s (%s)' % (jsonname, sha))
    elif verbose:
        print ('SAME %s (%s)' % (jsonname, sha))

if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('--root', default=os.path.dirname(os.path.abspath(__file__)))
    p.add_argument('--json', default=None, help='Defaults to <root>/json')
    p.add_argument('-v', '--verbose', action='store_true', help='Report unchanged books')
    args = p.parse_args()

    jsondir = args.json or os.path.join(args.root, 'json')
    os.makedirs(jsondir, exist_ok=True)

    for fname in sorted(os.listdir(args.root)):
        if fname.endswith('.zip'):
            process(os.path.join(args.root, fname), jsondir, args.verbose)
