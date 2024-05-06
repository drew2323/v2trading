#!/bin/bash

# Define the location where you want to store your .env file
ENV_FILE="/c/Projects/.env"

# Optionally clear the .env file to start fresh
> $ENV_FILE

VARIABLES_TO_INCLUDE=("ACCOUNT1_LIVE_API_KEY
ACCOUNT1_LIVE_SECRET_KEY
ACCOUNT1_LIVE_FEED
ACCOUNT1_PAPER_API_KEY
ACCOUNT1_PAPER_SECRET_KEY
ACCOUNT1_PAPER_FEED
ACCOUNT2_PAPER_API_KEY
ACCOUNT2_PAPER_SECRET_KEY
ACCOUNT2_PAPER_FEED")

for var in $VARIABLES_TO_INCLUDE 
do 
    printenv | grep $var >> $ENV_FILE
done


echo "dotenv file created at $ENV_FILE"