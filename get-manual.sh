#!/bin/sh

# Get the HTML format of the manual
# Download Page: https://www.gnu.org/software/c-intro-and-ref/

set -e

download_url='https://www.gnu.org/software/c-intro-and-ref/manual/c-intro-and-ref.html_node.tar.gz'
dest_dir='./gnu-c-manual-html'

mkdir --parents $dest_dir
wget --quiet --output-document - $download_url | tar -xz -C $dest_dir

echo "Manual downloaded to '$dest_dir'"
