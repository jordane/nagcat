#!/bin/bash

PIECE_DIR="./pieces"
OUT_FILE="./combined.min.js"

./js_minimize.py ${PIECE_DIR}/* > ${OUT_FILE}
