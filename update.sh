#!/bin/bash

cd deployment
git pull origin main
cd ..
git add deployment
git commit -m "Update submodule to the latest version"
git push