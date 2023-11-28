#!/usr/bin/env bash

# Get the HTML format of the manual
# Download Page: https://www.gnu.org/software/c-intro-and-ref/

download_url='https://www.gnu.org/software/c-intro-and-ref/manual/c-intro-and-ref.html_node.tar.gz'
dest_dir='./gnu-c-manual'

[ -d $dest_dir ] || mkdir $dest_dir

wget -q -O - $download_url | tar -xz -C $dest_dir
echo "Manual downloaded"
