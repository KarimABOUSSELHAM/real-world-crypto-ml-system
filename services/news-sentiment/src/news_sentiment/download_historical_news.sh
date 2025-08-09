#!/bin/bash

# Git clone the repo which includes the historical news
git clone https://github.com/soheilrahsaz/cryptoNewsDataset.git

# Uncompress the .rar file which we need
unar cryptoNewsDataset/csvOutput/cryptopanic_news.rar -o data/

# Remove the cloned git repo 
rm -rf cryptoNewsDataset