#!/bin/bash


game_name="$1"  # The first command-line argument represents the path to the folder

wieght_file="$2"  # The second command-line argument represents the path to the weight file name

cov="$3"

# Check if the path is provided
if [ -z "$game_name" ]; then
    echo "Usage: ./script.sh <game_name>"
    exit 1
fi

cd ..

folder_names=$(find games/"$game_name"/mutants/* -type d -maxdepth 1 -exec basename {} \;)

for ((counter=18; counter<=18; counter++)); do
  echo "Run # '$counter'"
  # Use the folder names in a command
  coverage run --branch run.py --agent=merlin  --mode=eval --exp_name=clean --weights_dir="$game_name"-wieghts/"$wieght_file" --game=$game_name --mutant=baseline --tries=20 --score=$cov
  coverage html -i

  # Name of the folder to be created
  run_folder_name=logs/coverage-logs/merlin/"$game_name"/decision/run_"$counter"

  # Create the folder if it doesn't exist
  if [ ! -d "$run_folder_name" ]; then
      mkdir "$run_folder_name"
      echo "Folder '$run_folder_name' created."
  else
      echo "Folder '$run_folder_name' already exists."
  fi

  # Move all .tsv files to the created folder
  mv htmlcov/* "$run_folder_name"/


  coverage run run.py --agent=merlin --mode=eval --exp_name=clean --weights_dir="$game_name"-wieghts/"$wieght_file" --game=$game_name --mutant=baseline --tries=20 --score=10
  coverage html -i

  # Name of the folder to be created
  run_folder_name=logs/coverage-logs/merlin/"$game_name"/statement/run_"$counter"

  # Create the folder if it doesn't exist
  if [ ! -d "$run_folder_name" ]; then
      mkdir "$run_folder_name"
      echo "Folder '$run_folder_name' created."
  else
      echo "Folder '$run_folder_name' already exists."
  fi

  # Move all .tsv files to the created folder
  mv htmlcov/* "$run_folder_name"/

  echo "All files moved to '$run_folder_name' folder."

done
read userInput