#!/bin/bash

TARGET=training/
PROCESSED=saved_ckpt/

inotifywait -m -e create -e moved_to --format "%f" $TARGET \
        | while read FILENAME
                do
                        echo Detected $FILENAME, moving and zipping
                        cp "$TARGET/$FILENAME" "$PROCESSED/$FILENAME"
                done
~                                                                               
~                                                                               
~                                                                               
~                                                  
